# Royal Nepal Restaurant Web Application

![Restaurant Logo](static/img/logo.png)

## Overview
A full-featured restaurant management system built with Django, featuring online ordering, table reservations, gift card management, and a comprehensive admin panel. This application provides both customer-facing features and restaurant management capabilities.

## Features

### Customer Features
- **Online Food Ordering**
  - Browse menu by categories
  - Add items to cart
  - Apply rewards points
  - Multiple payment options (Credit Card, PayPal, Pay at Pickup)
  - Order tracking and history

- **Table Reservations**
  - Book tables for specific dates and times
  - Manage and view reservation history
  - Special requests handling
  - Automatic confirmation emails

- **Gift Cards**
  - Purchase digital gift cards
  - Check gift card balance
  - Redeem gift cards for orders
  - Gift card transaction history

- **User Accounts**
  - Personal profile management
  - Order history
  - Rewards points tracking
  - Saved preferences
  - Transaction history

### Restaurant Admin Features
- **Order Management**
  - Real-time order notifications
  - Order status updates
  - Kitchen display system
  - Order history and analytics

- **Reservation Management**
  - Approve/reject reservations
  - Table management
  - Guest tracking
  - Special requests handling

- **Menu Management**
  - Add/edit menu items
  - Category management
  - Price updates
  - Item availability control

- **Payment Management**
  - Transaction tracking
  - Refund processing
  - Payment method management
  - Financial reporting

- **Gift Card Management**
  - Issue and track gift cards
  - Balance management
  - Transaction history
  - Validation system

## Technical Architecture

### Backend
- **Framework**: Django 4.2.17
- **Database**: SQLite (development) / PostgreSQL (production)
- **Authentication**: Django built-in auth system
- **File Storage**: Django local storage

### Frontend
- **Template Engine**: Django Templates
- **CSS Framework**: Bootstrap 5
- **JavaScript Libraries**:
  - jQuery 3.6.0
  - Stripe.js for payments
  - Chart.js for analytics
  - DataTables for table management

### Payment Integration
- Stripe for card payments
- PayPal integration
- Gift card system

### Email System
- SMTP integration
- Email templates
- Order confirmations
- Reservation notifications

## Project Structure
```
restaurant_project/
├── accounts/            # User account management
├── core/               # Core functionality and base templates
├── menu/              # Menu management
├── orders/            # Order processing and management
├── reservations/      # Table reservation system
├── restaurant_admin/  # Admin dashboard and controls
├── giftcards/         # Gift card system
├── static/           # Static files (CSS, JS, images)
├── templates/        # HTML templates
└── main/            # Project settings and configurations
```

## Setup and Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager
- Virtual environment (recommended)

### Installation Steps
1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/restaurant-project.git
   cd restaurant-project
   ```

2. Create and activate virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   # or
   .venv\Scripts\activate  # Windows
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Setup environment variables:
   Create a `.env` file with:
   ```
   SECRET_KEY=your_secret_key
   DEBUG=True
   STRIPE_PUBLIC_KEY=your_stripe_public_key
   STRIPE_SECRET_KEY=your_stripe_secret_key
   EMAIL_HOST=your_email_host
   EMAIL_HOST_USER=your_email
   EMAIL_HOST_PASSWORD=your_email_password
   ```

5. Run migrations:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. Create superuser:
   ```bash
   python manage.py createsuperuser
   ```

7. Run the development server:
   ```bash
   python manage.py runserver
   ```

## Testing
Run tests with:
```bash
python manage.py test
```

## Deployment
- Configure production settings
- Set DEBUG=False
- Set up proper database
- Configure static files serving
- Set up HTTPS
- Configure email settings
- Set up proper domain

## API Endpoints
- `/api/menu/` - Menu items and categories
- `/api/orders/` - Order management
- `/api/reservations/` - Reservation handling
- `/api/giftcards/` - Gift card operations
- `/api/accounts/` - User account management

## Security Features
- CSRF protection
- XSS prevention
- SQL injection prevention
- Secure password handling
- Session security
- Rate limiting

## Backup and Recovery
- Database backup system
- File storage backup
- Recovery procedures
- Data retention policies

## Performance Optimization
- Database query optimization
- Caching implementation
- Static file compression
- Image optimization
- Lazy loading

## Contributing
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## Versioning
This project uses [SemVer](http://semver.org/) for versioning. For available versions, see the tags on this repository.

## License
This project is licensed under the MIT License - see below for details:

```
MIT License

Copyright (c) 2025 Royal Nepal Restaurant

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## Contact
- Website: [royalnepal.com](https://royalnepal.com)
- Email: contact@royalnepal.com
- Phone: +1 5589 55488 55

## Support
For support, email support@royalnepal.com or call our customer service line.

## Acknowledgments
- Bootstrap team for the UI framework
- Stripe for payment processing
- All other open-source contributors

## Project Status
Active development - Version 1.0.0