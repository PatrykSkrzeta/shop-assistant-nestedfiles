from flask import render_template, redirect, url_for, request, flash, send_file
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from app import app, login_manager
from models import User, Product, Order, OrderItem
from forms import LoginForm, ProductForm, OrderForm, OrderItemForm
from datetime import *
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os


@login_manager.user_loader
def load_user(user_id):
    return User.objects(email=user_id).first()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.objects(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            flash('User has login succesfully ','info')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password')

    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('User logout successfully','info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/customers', methods=['GET'])
@login_required
def customers():
    search_query = request.args.get('search', '').strip()
    filter_date = request.args.get('date', '').strip()

    
    if search_query:
        filtered_orders = Order.objects(last_name__icontains=search_query)
    elif filter_date:
        try:
            filter_date = datetime.strptime(filter_date, '%Y-%m-%d')
            filtered_orders = Order.objects(date_added=filter_date)
        except ValueError:
            flash('Invalid date format. Please use YYYY-MM-DD.')
            return redirect(url_for('customers'))
    else:
        filtered_orders = Order.objects()

    for order in filtered_orders:
        order.total_quantity = sum(item.quantity for item in order.order_items)

    total_orders = filtered_orders.count() - 3

    return render_template('customers.html', orders=filtered_orders, total_orders=total_orders)


@app.route('/customers/delete/<order_id>', methods=['POST'])
@login_required
def delete_order(order_id):
    order = Order.objects.get(id=order_id)
    order.delete()
    flash('Order deleted successfully','info')
    return redirect(url_for('customers'))

@app.route('/magazine', methods=['GET', 'POST'])
@login_required
def magazine():
    search_query = request.args.get('search', '').strip()

    if search_query:
        filtered_products = Product.objects(name__icontains=search_query)
    else:
        filtered_products = Product.objects()

    total_products = filtered_products.count()

    return render_template('magazine.html', products=filtered_products, total_products=total_products)


@app.route('/delete_product/<product_id>', methods=['POST'])
@login_required
def delete_product(product_id):
    product = Product.objects.get(id=product_id)
    product.delete()
    flash('Product deleted successfully','info')
    return redirect(url_for('magazine'))


@app.route('/addproduct', methods=['GET', 'POST'])
@login_required
def addproduct():
    form = ProductForm()
    if form.validate_on_submit():
        product = Product(
            name=form.name.data,
            category=form.category.data,
            product_type=form.product_type.data,
            value=form.value.data,
            price=form.price.data
        )
        product.save()
        flash('Product added successfully','info')
        return redirect(url_for('addproduct')) 
    return render_template('add_product.html', form=form)



@app.route('/customers/<order_id>')
@login_required
def order_details(order_id):
    try:
        order = Order.objects(id=order_id).first()
        if not order:
            flash('Order not found')
            return redirect(url_for('customers'))

        total_quantity = sum(item.quantity for item in order.order_items)

        return render_template('customers-details.html', order=order, total_quantity=total_quantity)
    except Exception as e:
        flash(f'An error occurred: {e}')
        return redirect(url_for('customers'))
    
@app.route('/addorder', methods=['GET', 'POST'])
@login_required
def addorder():
    form = OrderForm()
    if request.method == 'POST':
        if form.add_item.data:
            form.order_items.append_entry()
            return render_template('add_order.html', form=form)

        if form.submit.data:
            try:
                order_items = []
                total_order_price = 0

                for item in form.order_items.entries:
                    try:
                        product = Product.objects.get(name=item.product_name.data)
                        if product.value < item.quantity.data:
                            flash(f"Not enough stock for '{item.product_name.data}'. Available: {product.value}.")
                            return render_template('add_order.html', form=form)

                        total_price = item.quantity.data * product.price
                        total_order_price += total_price
                        order_item = OrderItem(
                            product=product,
                            product_name=product.name,
                            quantity=item.quantity.data,
                            total_price=total_price
                        )
                        order_items.append(order_item)

                        product.value -= item.quantity.data
                        product.save()
                    except Product.DoesNotExist:
                        flash(f"Product '{item.product_name.data}' does not exist.")
                        return render_template('add_order.html', form=form)

                
                discount = 0
                if total_order_price >= 500:
                    discount = total_order_price * 0.07 
                    total_order_price -= discount
                    flash('Discount has been set successfully', 'info')

                new_order = Order(
                    first_name=form.first_name.data,
                    last_name=form.last_name.data,
                    pesel=form.pesel.data,
                    contact=form.contact.data,
                    address=form.address.data,
                    order_items=order_items,
                    total_order_price=total_order_price,
                    discount=discount 
                )

                new_order.save()

                flash('Order placed successfully!')
                return redirect(url_for('addorder'))
            except Exception as e:
                flash(f"An error occurred while processing the order: {e}")

    return render_template('add_order.html', form=form)


@app.route('/download_pdf/<order_id>')
def download_pdf(order_id):
    order = Order.objects(id=order_id).first()
    if not order:
        return 'Order not found', 404

    pdf_dir = 'shopassistant/pdf'
    os.makedirs(pdf_dir, exist_ok=True)
    pdf_path = os.path.join(pdf_dir, f"order_{order_id}.pdf")

    c = canvas.Canvas(pdf_path, pagesize=letter)

    # Define top margin
    top_margin = 30

    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 800 - top_margin, f"Order ID: {order_id}")

    c.setFont("Helvetica", 12)
    y = 750 - top_margin
    c.drawString(50, y, f"Date: {order.date_added.strftime('%Y-%m-%d %H:%M:%S')}")
    c.drawString(50, y-20, f"Customer: {order.first_name} {order.last_name}")
    c.drawString(50, y-40, f"Address: {order.address}")
    c.drawString(50, y-60, f"PESEL: {order.pesel}")
    c.drawString(50, y-80, f"Contact: {order.contact}")
    c.drawString(50, y-100, "-"*60)

    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y-120, "Product Name")
    c.drawString(250, y-120, "Quantity")
    c.drawString(350, y-120, "Total Price")

    y_start = y - 140
    for idx, item in enumerate(order.order_items):
        product_name = item.product_name
        quantity = item.quantity
        total_price = item.total_price

        c.setFont("Helvetica", 12)
        c.drawString(50, y_start - idx * 20, f"{product_name}")
        c.drawString(250, y_start - idx * 20, f"{quantity}")
        c.drawString(350, y_start - idx * 20, f"{total_price:.2f} $")

    c.drawString(50, y_start - len(order.order_items) * 20 - 20, "-"*60)

    if order.discount > 0:
        c.setFont("Helvetica-Bold", 12)
        c.drawString(250, y_start - len(order.order_items) * 20 - 40, "Discount:")
        c.setFont("Helvetica", 12)
        c.drawString(350, y_start - len(order.order_items) * 20 - 40, f"-{order.discount:.2f} $")

    c.setFont("Helvetica-Bold", 14)
    c.drawString(250, y_start - len(order.order_items) * 20 - 60, "Total:")
    c.setFont("Helvetica", 14)
    c.drawString(350, y_start - len(order.order_items) * 20 - 60, f"{order.total_order_price:.2f} $")

    c.showPage()
    c.save()

    flash('PDF generated successfully', 'info')
    return send_file(pdf_path, as_attachment=True, download_name=f"order_{order_id}.pdf", mimetype='application/pdf')
    


if __name__ == '__main__':
    app.run(debug=True)
