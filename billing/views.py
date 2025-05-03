from rest_framework import viewsets, status
from rest_framework.response import Response
from django.core.mail import send_mail
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from .models import Bill, BillItem
from .serializers import BillSerializer
from inventory.models import Medicine
from django.core.mail import EmailMessage
import random
import string
from django.db.models import F


class BillingViewSet(viewsets.ModelViewSet):
    queryset = Bill.objects.all()
    serializer_class = BillSerializer

    def create(self, request, *args, **kwargs):
        try:
            user = request.user
            if not user.groups.filter(name="Staff").exists():
                return Response({'error': 'User not authorized to create bills'}, 
                            status=status.HTTP_403_FORBIDDEN)

            # Validate required fields
            if 'items' not in request.data or not isinstance(request.data['items'], list):
                return Response({'error': 'Items list is required'}, 
                            status=status.HTTP_400_BAD_REQUEST)

            # Prepare data for Bill and BillItem
            bill_data = {
                'staff_user': user.id,
                'customer_name': request.data.get('customer_name', ''),
                'customer_email': request.data.get('customer_email', ''),
                'customer_phone': request.data.get('customer_phone', ''),
                'billing_address': request.data.get('billing_address', ''),
                'total_amount': 0,  # Will be calculated
            }

            # Calculate the total amount and process items
            bill_items_data = []
            total_amount = 0
            medicines_to_update = {}  # To track medicines and their stock changes
            
            for item_data in request.data['items']:
                # Validate item fields
                required_item_fields = ['medicine_name', 'quantity', 'packaging_type']
                for field in required_item_fields:
                    if field not in item_data:
                        return Response({'error': f'{field} is required for all items'}, 
                                        status=status.HTTP_400_BAD_REQUEST)

                # Validate packaging type
                if item_data['packaging_type'] not in dict(BillItem.PACKAGING_TYPES):
                    return Response({'error': f'Invalid packaging type: {item_data["packaging_type"]}'}, 
                                    status=status.HTTP_400_BAD_REQUEST)

                try:
                    medicine = Medicine.objects.get(name=item_data['medicine_name'])
                except Medicine.DoesNotExist:
                    return Response({'error': f'Medicine {item_data["medicine_name"]} not found'}, 
                                    status=status.HTTP_400_BAD_REQUEST)

                # Get pricing
                price_field = f'price_{item_data["packaging_type"]}'
                unit_price = getattr(medicine, price_field, None)
                
                if unit_price is None:
                    return Response({'error': f'Price not available for {item_data["packaging_type"]} packaging'}, 
                                    status=status.HTTP_400_BAD_REQUEST)

                quantity = int(item_data['quantity'])
                
                # Check stock availability before proceeding
                if medicine.stock < quantity:
                    return Response({'error': f'Not enough stock for {medicine.name}. Available: {medicine.stock}, Requested: {quantity}'}, 
                                status=status.HTTP_400_BAD_REQUEST)
                
                item_total = unit_price * quantity
                total_amount += item_total

                # Track stock changes
                if medicine.id in medicines_to_update:
                    medicines_to_update[medicine.id]['quantity'] += quantity
                else:
                    medicines_to_update[medicine.id] = {
                        'medicine': medicine,
                        'quantity': quantity
                    }

                # Prepare bill item data
                bill_items_data.append({
                    'medicine': medicine,
                    'quantity': quantity,
                    'packaging_type': item_data['packaging_type'],
                    'unit_price': unit_price,
                    'total_price': item_total
                })

            # Add the calculated total amount
            bill_data['total_amount'] = total_amount

            # Create the bill instance using the serializer
            serializer = self.get_serializer(data=bill_data)
            serializer.is_valid(raise_exception=True)
            bill = serializer.save()

            # Now create the BillItem instances
            for item_data in bill_items_data:
                BillItem.objects.create(
                    bill=bill,
                    medicine_id=item_data['medicine'].id,
                    quantity=item_data['quantity'],
                    packaging_type=item_data['packaging_type'],
                    unit_price=item_data['unit_price'],
                    total_price=item_data['total_price']
                )

            # Update medicine stocks
            for medicine_id, data in medicines_to_update.items():
                medicine = data['medicine']
                quantity = data['quantity']
                
                # Use F() to avoid race conditions
                Medicine.objects.filter(id=medicine_id).update(
                    stock=F('stock') - quantity
                )
                
                # Refresh the medicine instance and check stock/expiry
                medicine.refresh_from_db()
                medicine.check_stock_and_expiry()

            # Send email with PDF invoice
            self._send_invoice_email(bill, bill_items_data)

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({'error': str(e)}, 
                        status=status.HTTP_400_BAD_REQUEST)

    # def _send_invoice_email(self, bill, bill_items_data):
    def _send_invoice_email(self, bill, bill_items_data):
        subject = f"Invoice #{bill.invoice_number} - Your Purchase Details"

        # Construct the email body with HTML formatting
        message = f"""
        <html>
        <head>
        <style>
            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 15px 0;
            }}
            th, td {{
                padding: 8px;
                text-align: left;
                border-bottom: 1px solid #ddd;
            }}
            th {{
                background-color: #f2f2f2;
            }}
            .total-row {{
                font-weight: bold;
                border-top: 2px solid #000;
            }}
        </style>
        </head>
        <body>
            <p>Dear {bill.customer_name},</p>
            <p>Your invoice #{bill.invoice_number} is ready. Below are the details of your purchase:</p>
            
            <table>
                <thead>
                    <tr>
                        <th>Product Name</th>
                        <th>Qty</th>
                        <th>Unit Price</th>
                        <th>Total Price</th>
                    </tr>
                </thead>
                <tbody>
        """

        # Add table rows for each item
        for item in bill_items_data:
            message += f"""
                    <tr>
                        <td>{item['medicine'].name}</td>
                        <td>{item['quantity']}</td>
                        <td>{item['unit_price']}</td>
                        <td>{item['total_price']}</td>
                    </tr>
        """

        # Add total row
        message += f"""
                    <tr class="total-row">
                        <td>Total Amount</td>
                        <td></td>
                        <td></td>
                        <td>{bill.total_amount}</td>
                    </tr>
                </tbody>
            </table>
            
            <p>Thank you for shopping with us!</p>
            <p>Best regards,<br>Your Store Name</p>
        </body>
        </html>
        """


        # Generate PDF invoice
        pdf_file = self._generate_pdf_invoice(bill, bill_items_data)

        # Send the email with the PDF attached
        email = EmailMessage(
            subject,
            message,
            'noreply@yourstore.com',
            [bill.customer_email]
        )
        email.attach(f'invoice_{bill.invoice_number}.pdf', pdf_file.getvalue(), 'application/pdf')
        email.content_subtype = "html"
        email.send(fail_silently=False)

    def _generate_pdf_invoice(self, bill, bill_items_data):
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)

        # Title with invoice number
        c.setFont("Helvetica-Bold", 16)
        c.drawString(200, 750, f"Invoice #{bill.invoice_number}")

        # Customer details
        c.setFont("Helvetica", 12)
        c.drawString(50, 730, f"Customer Name: {bill.customer_name}")
        c.drawString(50, 710, f"Customer Email: {bill.customer_email}")
        c.drawString(50, 690, f"Billing Address: {bill.billing_address}")
        c.drawString(50, 670, f"Phone: {bill.customer_phone}")
        c.drawString(50, 650, f"Date: {bill.created_at.strftime('%Y-%m-%d %H:%M:%S')}")

        # Product table header
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, 620, "Product Name")
        c.drawString(250, 620, "Quantity")
        c.drawString(350, 620, "Unit Price")
        c.drawString(450, 620, "Total Price")
        c.line(50, 615, 550, 615)

        # Product details
        c.setFont("Helvetica", 12)
        y_position = 590
        for item in bill_items_data:
            c.drawString(50, y_position, item['medicine'].name)
            c.drawString(250, y_position, str(item['quantity']))
            c.drawString(350, y_position, f"${item['unit_price']:.2f}")
            c.drawString(450, y_position, f"${item['total_price']:.2f}")
            y_position -= 20

        # Total amount
        c.setFont("Helvetica-Bold", 12)
        c.drawString(350, y_position - 30, f"Total Amount: ${bill.total_amount:.2f}")

        # Footer with invoice number
        c.setFont("Helvetica", 10)
        c.drawString(50, 50, f"Invoice Number: {bill.invoice_number}")
        c.drawString(50, 30, "Thank you for your business!")

        # Save PDF
        c.save()
        buffer.seek(0)
        return buffer