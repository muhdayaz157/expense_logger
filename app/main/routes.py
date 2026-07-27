from flask import Blueprint, render_template, request, redirect, url_for, flash
from sqlalchemy import or_
from datetime import datetime

from app import db
from app.models import Expense


main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():

    # URL se search, category aur sort values receive kar rahe hain
    search = request.args.get("search", "").strip()
    category = request.args.get("category", "").strip()
    sort = request.args.get("sort", "newest")

    # Database query start kar rahe hain
    query = Expense.query

    # Search filter
    if search:
     query = query.filter(
        or_(
            Expense.title.ilike(f"%{search}%"),
            Expense.note.ilike(f"%{search}%")
        )
    )

    # Category filter
    if category:
        query = query.filter(
            Expense.category == category
        )

    # Sorting
    if sort == "oldest":
        query = query.order_by(Expense.id.asc())

    elif sort == "amount_high":
        query = query.order_by(Expense.amount.desc())

    elif sort == "amount_low":
        query = query.order_by(Expense.amount.asc())

    else:
        # Default: newest expense first
        query = query.order_by(Expense.id.desc())

    # Filtered expenses database se nikal rahe hain
    expenses = query.all()


    # ========================================
    # Dashboard Statistics
    # ========================================

    # Total spending calculate kar rahe hain
    total_expenses = sum(
        expense.amount for expense in expenses
    )

    # Total expense records
    expense_count = len(expenses)

    # Average expense
    if expense_count > 0:
        average_expense = total_expenses / expense_count
    else:
        average_expense = 0


    # ========================================
    # Available Categories
    # ========================================

    categories = db.session.query(
        Expense.category
    ).distinct().all()

    categories = [
        item[0]
        for item in categories
        if item[0]
    ]


    # ========================================
    # Category-wise Spending
    # ========================================

    category_totals = {}

    # Har expense ko check kar rahe hain
    for expense in expenses:

        # Expense ki category le rahe hain
        # Agar category empty ho to Uncategorized
        category_name = expense.category or "Uncategorized"

        # Agar category pehli baar mili hai
        # to uska total 0 se start hoga
        if category_name not in category_totals:
            category_totals[category_name] = 0

        # Amount ko category ke total mein add kar rahe hain
        category_totals[category_name] += expense.amount


    # Categories ko highest spending se
    # lowest spending ke order mein arrange kar rahe hain
    category_totals = dict(
        sorted(
            category_totals.items(),
            key=lambda item: item[1],
            reverse=True
        )
    )


    # ========================================
    # Send Data to index.html
    # ========================================

    return render_template(
        "index.html",
        expenses=expenses,
        total_expenses=total_expenses,
        expense_count=expense_count,
        average_expense=average_expense,
        categories=categories,
        category_totals=category_totals,
        search=search,
        selected_category=category,
        selected_sort=sort
    )
@main_bp.route("/create", methods=["GET", "POST"])
def create_expense():

    if request.method == "POST":

        # Form se data receive kar rahe hain
        title = request.form.get("title", "").strip()
        amount = request.form.get("amount", "").strip()
        category = request.form.get("category", "").strip()
        date = request.form.get("date", "").strip()
        note = request.form.get("note", "").strip()


        # ========================================
        # Basic Validation
        # ========================================

        if not title:
            flash("Please enter an expense title.", "danger")
            return render_template("create.html")

        if not amount:
            flash("Please enter an expense amount.", "danger")
            return render_template("create.html")

        if not category:
            flash("Please select a category.", "danger")
            return render_template("create.html")

        if not date:
            flash("Please select a date.", "danger")
            return render_template("create.html")


        # ========================================
        # Date Validation
        # ========================================

        try:

            # Date ka exact format check
            if len(date) != 10:
                raise ValueError

            # YYYY-MM-DD format check
            if date[4] != "-" or date[7] != "-":
                raise ValueError

            # Date ko Python date object mein convert kar rahe hain
            date_object = datetime.strptime(
                date,
                "%Y-%m-%d"
            ).date()

            # Current year
            current_year = datetime.now().year

            # Sirf 2000 se next year tak ki dates allow
            if date_object.year < 2000 or date_object.year > current_year + 1:

                flash(
                    f"Year must be between 2000 and {current_year + 1}.",
                    "danger"
                )

                return render_template("create.html")


        except ValueError:

            flash(
                "Please enter a valid date in YYYY-MM-DD format.",
                "danger"
            )

            return render_template("create.html")


        # ========================================
        # Amount Validation
        # ========================================

        try:

            amount = float(amount)

        except ValueError:

            flash(
                "Amount must be a valid number.",
                "danger"
            )

            return render_template("create.html")


        if amount <= 0:

            flash(
                "Amount must be greater than £0.",
                "danger"
            )

            return render_template("create.html")


        # ========================================
        # Create Expense
        # ========================================

        expense = Expense(
            title=title,
            amount=amount,
            category=category,

            # Validated date object save hoga
            date=date_object,

            note=note
        )

        db.session.add(expense)
        db.session.commit()


        flash(
            "Expense added successfully!",
            "success"
        )

        return redirect(
            url_for("main.index")
        )


    return render_template("create.html")

@main_bp.route("/edit/<int:id>", methods=["GET", "POST"])
def edit_expense(id):

    expense = Expense.query.get_or_404(id)


    if request.method == "POST":

        # Form se updated data receive kar rahe hain
        title = request.form.get("title", "").strip()
        amount = request.form.get("amount", "").strip()
        category = request.form.get("category", "").strip()
        date = request.form.get("date", "").strip()
        note = request.form.get("note", "").strip()


        # ========================================
        # Basic Validation
        # ========================================

        if not title:

            flash(
                "Please enter an expense title.",
                "danger"
            )

            return render_template(
                "edit.html",
                expense=expense
            )


        if not amount:

            flash(
                "Please enter an expense amount.",
                "danger"
            )

            return render_template(
                "edit.html",
                expense=expense
            )


        if not category:

            flash(
                "Please select a category.",
                "danger"
            )

            return render_template(
                "edit.html",
                expense=expense
            )


        if not date:

            flash(
                "Please select a date.",
                "danger"
            )

            return render_template(
                "edit.html",
                expense=expense
            )


        # ========================================
        # Date Validation
        # ========================================

        try:

            # Exact format check
            if len(date) != 10:
                raise ValueError

            # YYYY-MM-DD format check
            if date[4] != "-" or date[7] != "-":
                raise ValueError

            # Date convert
            date_object = datetime.strptime(
                date,
                "%Y-%m-%d"
            ).date()

            # Current year
            current_year = datetime.now().year

            # Year range check
            if date_object.year < 2000 or date_object.year > current_year + 1:

                flash(
                    f"Year must be between 2000 and {current_year + 1}.",
                    "danger"
                )

                return render_template(
                    "edit.html",
                    expense=expense
                )


        except ValueError:

            flash(
                "Please enter a valid date in YYYY-MM-DD format.",
                "danger"
            )

            return render_template(
                "edit.html",
                expense=expense
            )


        # ========================================
        # Amount Validation
        # ========================================

        try:

            amount = float(amount)

        except ValueError:

            flash(
                "Amount must be a valid number.",
                "danger"
            )

            return render_template(
                "edit.html",
                expense=expense
            )


        if amount <= 0:

            flash(
                "Amount must be greater than £0.",
                "danger"
            )

            return render_template(
                "edit.html",
                expense=expense
            )


        # ========================================
        # Update Expense
        # ========================================

        expense.title = title
        expense.amount = amount
        expense.category = category

        # Validated date save kar rahe hain
        expense.date = date_object

        expense.note = note


        db.session.commit()


        flash(
            "Expense updated successfully!",
            "success"
        )

        return redirect(
            url_for("main.index")
        )


    return render_template(
        "edit.html",
        expense=expense
    )
@main_bp.route("/delete/<int:id>", methods=["POST"])
def delete_expense(id):

    expense = Expense.query.get_or_404(id)

    db.session.delete(expense)
    db.session.commit()

    flash("Expense deleted successfully!", "success")

    return redirect(url_for("main.index"))