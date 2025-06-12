from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Expense, Category
from .forms import ExpenseForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
import plotly.express as px
import pandas as pd

def signup_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('expense_list')
    else:
        form = UserCreationForm()
    return render(request, 'signup.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('expense_list')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def expense_list(request):
    expenses = Expense.objects.filter(user=request.user).order_by('-date')
    return render(request, 'expense_list.html', {'expenses': expenses})

@login_required
def add_expense(request):
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.user = request.user
            expense.save()
            return redirect('expense_list')
    else:
        form = ExpenseForm()
    return render(request, 'expense_form.html', {'form': form})

@login_required
def edit_expense(request, pk):
    expense = get_object_or_404(Expense, pk=pk, user=request.user)
    if request.method == 'POST':
        form = ExpenseForm(request.POST, instance=expense)
        if form.is_valid():
            form.save()
            return redirect('expense_list')
    else:
        form = ExpenseForm(instance=expense)
    return render(request, 'expense_form.html', {'form': form})

@login_required
def delete_expense(request, pk):
    expense = get_object_or_404(Expense, pk=pk, user=request.user)
    if request.method == 'POST':
        expense.delete()
        return redirect('expense_list')
    return render(request, 'delete_confirm.html', {'expense': expense})

@login_required
def dashboard(request):
    expenses = Expense.objects.filter(user=request.user)
    if not expenses.exists():
        return render(request, 'dashboard.html', {'no_data': True})

    df = pd.DataFrame(list(expenses.values('date', 'amount', 'category__name')))
    df['date'] = pd.to_datetime(df['date'])
    df['month'] = df['date'].dt.to_period('M').astype(str)
    df['weekday'] = df['date'].dt.day_name()

    # Pie Chart: Category-wise spend
    pie_chart = px.pie(df, names='category__name', values='amount', title='Expenses by Category').to_html(full_html=False)

    # Bar Chart: Monthly spend
    monthly = df.groupby('month')['amount'].sum().reset_index()
    bar_chart = px.bar(monthly, x='month', y='amount', title='Monthly Expenses', color='amount').to_html(full_html=False)

    # Line Chart: Daily spending trend
    daily = df.groupby('date')['amount'].sum().reset_index()
    line_chart = px.line(daily, x='date', y='amount', title='Daily Spending Trend', markers=True).to_html(full_html=False)

    # Donut Chart: Category-wise spend (alternative to pie)
    donut_chart = px.pie(df, names='category__name', values='amount', hole=0.4, title='Expenses by Category (Donut)').to_html(full_html=False)

    # KPI: Total spend this month
    this_month = pd.Timestamp.now().strftime('%Y-%m')
    total_spend_month = monthly[monthly['month'] == this_month]['amount'].sum() if this_month in monthly['month'].values else 0

    # KPI: Most expensive category
    cat_sum = df.groupby('category__name')['amount'].sum()
    top_category = cat_sum.idxmax() if not cat_sum.empty else 'N/A'
    top_category_amt = cat_sum.max() if not cat_sum.empty else 0

    # KPI: Highest single expense
    max_expense = df['amount'].max() if not df.empty else 0

    # KPI: Number of expenses
    num_expenses = len(df)

    return render(request, 'dashboard.html', {
        'pie_chart': pie_chart,
        'bar_chart': bar_chart,
        'line_chart': line_chart,
        'donut_chart': donut_chart,
        'total_spend_month': total_spend_month,
        'top_category': top_category,
        'top_category_amt': top_category_amt,
        'max_expense': max_expense,
        'num_expenses': num_expenses,
    })