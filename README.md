# Smart Electronics Inventory Management System

A comprehensive Django-based inventory management system designed for electronics retail businesses with advanced features including role-based access control, real-time stock tracking, purchase order management, and automated notifications.

## 🚀 Features

### Core Inventory Management
- **Product Management**: Track 800+ electronics products with SKU, brand, pricing, and warranty information
- **Category System**: Organize products across multiple categories (Smartphones, Laptops, Tablets, Accessories, etc.)
- **Stock Control**: Real-time inventory tracking with automated stock in/out logs
- **Multi-level Pricing**: Track purchase price, selling price, profit margins, and profit percentages
- **Active/Inactive Status**: Soft delete products without losing historical data

### Order Management
- **Complete Order Processing**: Draft → Confirmed → Paid → Cancelled workflow
- **Automated Bill Generation**: Unique bill numbers (BILL-00001 format)
- **Customer Information**: Name, email, phone, complete address with Indian state selection
- **Order Items**: Multiple products per order with quantity and pricing
- **Warranty Tracking**: Automatic warranty start date on payment
- **Payment Status**: Track pending, paid, and failed payments
- **Order Receipts**: PDF receipt generation for customers

### Purchase Order System
- **Purchase Requests**: Staff can request product purchases from suppliers
- **Approval Workflow**: Admin approval required (Pending → Approved → Rejected)
- **Purchase Orders**: Automated PO creation after approval but saved as draft to add expected delivery
- **Delivery Tracking**: Draft → Ordered → Shipped → In Transit → Delivered → Delayed
- **Expected vs Actual Delivery**: Track delivery performance
- **Warehouse Management**: Configurable warehouse addresses
- **Cost Tracking**: Total cost calculation per purchase order

### Supplier Management
- **Vendor Database**: Contact person, phone, email, address
- **Category Mapping**: Track which categories each supplier provides
- **Active/Inactive Status**: Manage supplier relationships
- **Performance Analytics**: Supplier value reports and activity tracking
- **Multi-category Support**: Suppliers can provide multiple product categories

### Stock Management
- **Stock Logs**: Complete audit trail of all stock movements
- **User Tracking**: Know who performed each stock operation
- **Stock In/Out**: Separate workflows for receiving and dispatching inventory
- **Low Stock Alerts**: Configurable threshold-based notifications
- **Out of Stock Reports**: Identify products requiring immediate attention
- **Stock Value Calculation**: Real-time inventory valuation
- **Dead Stock Identification**: Find slow-moving or obsolete inventory

### Notification System
- **Real-time Alerts**: Product, category, supplier, stock, purchase, and order notifications
- **Role-based Notifications**: Different alerts for Admin, Manager, and Staff
- **Notification Types**: Info, Success, Warning, Danger classifications
- **Read/Unread Status**: Track which notifications have been viewed
- **Activity Tracking**: Know who created each notification
- **Dashboard Integration**: Notification bell with unread count

### Reporting & Analytics
- **Low Stock Report**: Products below reorder threshold
- **Reorder Report**: Automated purchase suggestions
- **Stock Value Report**: Total inventory valuation
- **Dead Stock Report**: Identify non-moving inventory
- **Average Price Report**: Category-wise pricing analysis
- **Top Value Products**: Highest value inventory items
- **Supplier Performance**: Value-based supplier rankings
- **Category Analysis**: Products per category, categories without products
- **Order Analytics**: Order attention reports, pending payments
- **Export Options**: CSV, Excel, and PDF exports for all reports

### User Management & Security
- **Role-based Access Control**: Admin, Manager, Staff roles with different permissions
- **Group Management**: Users assigned to Admin, Manager, or Staff groups
- **Custom Dashboards**: Role-specific dashboards with relevant metrics
- **User Activity Tracking**: All actions logged with user information
- **Password Management**: Secure password reset functionality
- **Session Management**: Secure authentication and authorization

### Advanced Features
- **Responsive Design**: Mobile-friendly interface with Bootstrap 5
- **Search & Filters**: Advanced filtering across all modules
- **Pagination**: Efficient data loading for large datasets
- **Bulk Operations**: CSV import support for products, orders, and purchases
- **Email Notifications**: SMTP integration for automated emails
- **Task Scheduling**: APScheduler for recurring tasks
- **Audit Trail**: Complete history of all database changes
- **Data Export**: Multiple format support (CSV, Excel, PDF)

## 🛠️ Tech Stack

### Backend
- **Framework**: Django 6.0.1
- **Database**: SQLite (development)
- **ORM**: Django ORM with optimized queries
- **Task Scheduler**: APScheduler 3.11.2
- **PDF Generation**: ReportLab 4.4.9

### Frontend
- **UI Framework**: Bootstrap 5.3.2
- **Icons**: Bootstrap Icons 1.11.1, Font Awesome 6.4.2
- **Forms**: Django Crispy Forms with Bootstrap 5
- **JavaScript**: Vanilla JS for interactivity

### Storage & Media
- **Static Files**: WhiteNoise 6.12.0
- **Image Processing**: Pillow 12.1.0


### Additional Libraries
- **Excel Support**: openpyxl 3.1.5
- **HTTP Requests**: requests 2.32.5
- **Timezone**: tzlocal 5.3.1

## 📦 Installation

### Prerequisites
- Python 3.11 or higher
- pip package manager
- Virtual environment tool
- Git

### Local Development Setup

1. **Clone the repository**
```bash
git clone https://github.com/YOUR_USERNAME/electronics-inventory.git
cd electronics-inventory
```

2. **Create and activate virtual environment**
```bash
python -m venv venv

# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Create environment file**

Create `.env` file in project root:
```env
INVENT_KEY=your-django-secret-key
EMAIL_USER=your-email@gmail.com
EMAIL_PASS=your-email-app-password
```

5. **Run migrations**
```bash
python manage.py migrate
```

6. **Create superuser**
```bash
python manage.py createsuperuser
```

7. **Create user groups**
```bash
python manage.py shell
```
```python
from django.contrib.auth.models import Group
Group.objects.create(name='Admin')
Group.objects.create(name='Manager')
Group.objects.create(name='Staff')
exit()
```
8. **Add data into models**
```bash
python manage.py import_bulk_products // import products , category and supplier data // takes around 5-10 minutes
python manage.py import_bulk_purchases // import purchase request and purchase order // takes around 5-10 minutes
python manage.py import_bulk_orders // import order and orderitem // takes around 5-10 minutes
python manage.py import_bulk_stocklogs // import stock // takes around 5 minutes
```

9. **Run development server**
```bash
python manage.py runserver
```

10. **Access the application**
- Main site: `http://localhost:8000`
- Admin panel: `http://localhost:8000/admin`

## 📁 Project Structure

```
electronics_inventory/
├── accounts/              # Authentication & authorization
├── dashboard/             # Role-specific dashboards
├── inventory/             # Core inventory management
├── orders/                # Order processing system
├── purchases/             # Purchase order management
├── suppliers/             # Vendor management
├── users/                 # User management
├── notifications/         # Alert system
├── settings_app/          # System configuration
├── templates/             # HTML templates
├── static/                # Static assets
├── media/                 # Uploaded files (local dev)
├── generated_data/        # Bulk import CSV files
├── requirements.txt       # Python dependencies
├── manage.py             # Django management script
└── README.md             # This file
```

## 👥 User Roles & Permissions

### Admin (Superuser)
- Full system access
- User management (create, update, delete users)
- System configuration
- All inventory operations
- Purchase order approval
- Complete reporting access
- Database management

### Manager
- Inventory management (products, categories, suppliers)
- Purchase request approval/rejection
- Purchase order management
- Order processing
- Stock control
- Advanced reporting
- Supplier management

### Staff
- Order creation and processing
- Stock in/out operations
- Purchase request creation
- Basic product viewing
- Limited reporting
- Customer management

## 🔧 Configuration

### Low Stock Threshold
Configure in `inventory/config.py`:
```python
def get_low_stock_threshold():
    return 10  # Adjust as needed
```

### Email Settings
Configure SMTP in `.env`:
```env
EMAIL_USER=your-email@gmail.com
EMAIL_PASS=your-app-specific-password
```

## 📊 Database Schema

### Key Models
- **Product**: 800+ electronics with pricing, warranty, stock
- **Category**: Product categorization
- **Supplier**: Vendor information and relationships
- **Order**: Customer orders with billing details
- **OrderItem**: Line items with warranty tracking
- **PurchaseRequest**: Staff purchase requests
- **PurchaseOrder**: Approved purchases with delivery tracking
- **StockLog**: Complete audit trail of stock movements
- **Notification**: System-wide alert system


## 📈 Usage Examples

### Adding Products
1. Navigate to Inventory Items dashboard
2. Click "Add Product"
3. Fill in SKU, name, brand, pricing, category, supplier
4. Upload product image
5. Set warranty period
6. Save

### Processing Orders
1. Go to Order Management
2. Click "Create Order"
3. Enter customer details
4. Add products with quantities
5. Confirm order
6. Mark as paid to activate warranties
7. Generate receipt PDF

### Managing Stock
1. Access Stock Control dashboard
2. Select "Stock In" or "Stock Out"
3. Choose product and quantity
4. Submit - stock log created automatically
5. View stock history for audit trail

### Purchase Workflow
1. Staff creates purchase request
2. Manager/Admin reviews in Purchase Orders
3. Approve or reject request
4. Approved requests auto-create purchase orders
5. Track delivery status
6. Stock updated on delivery

## 🔍 Key Features Explained

### Warranty System
- Warranty period stored per product
- Copied to order items on purchase
- Starts when order marked as "Paid"
- Automatic expiry calculation
- Check warranty status anytime

### Profit Calculation
- Automatic profit = selling price - purchase price
- Margin % = (profit / purchase price) × 100
- Calculated on save
- Displayed in dashboards

### Notification System
- Auto-created on key events
- Role-based visibility
- Real-time dashboard updates
- Mark as read functionality

### Stock Valuation
- Per product: purchase_price × quantity
- Total inventory value calculated
- Reports available by category

## 📝 License

Proprietary - All rights reserved

## 🙏 Acknowledgments

- Django framework and community
- Bootstrap for responsive UI
- ReportLab for PDF generation

---

**Version**: 1.0  
**Last Updated**: March 2026  
**Python**: 3.11+  
**Django**: 6.0.1
