# 🛒 Flask E-Commerce Platform with 3D Visuals & AI Analytics Chatbot

A full-stack, role-based E-Commerce web application built using **Flask**, **SQLite**, **Bootstrap 5**, and **Three.js**. The application supports distinct user roles (Admin, Seller, Buyer), complete Product CRUD functionality, buyer review management, dynamic graphs, and an interactive option-based analytics chatbot with floating 3D canvas visuals.

---

## 📌 Project Objectives

1. **Admin Access**: Predefined administrator authentication with access to a central analytics dashboard.
2. **Role-Based Workflows**:
   - **Admin**: Views live user counts, seller/buyer statistics, and platform performance graphs.
   - **Seller**: Registers, logs in, manages product inventory (Create, Read, Update, Delete), and views product buyer details.
   - **Buyer**: Registers, logs in, browses product catalog, leaves reviews/ratings, and places orders.
3. **Interactive Visuals & Chatbot**:
   - Dynamic 3D interactive background rendered using **Three.js**.
   - Option-based floating assistant providing real-time store analytics at the bottom-right of every page.

---

## 🛠️ Tech Stack

- **Backend**: Python 3, Flask, Flask-SQLAlchemy, Werkzeug (Password Hashing)
- **Database**: SQLite (`ecommerce.db`)
- **Frontend**: HTML5, Jinja2 Templates, Bootstrap 5, FontAwesome
- **3D Graphics & Charts**: Three.js, Chart.js

---

## 📂 Project Structure

```text
ecommerce_app/
│-- app.py
│-- README.md
└── templates/
    │-- base.html
    │-- home.html
    │-- about.html
    │-- contact.html
    │-- dashboard.html
    │-- product/
    │   │-- product_add.html
    │   │-- product_read.html
    │   │-- product_edit.html
    │   └── product_delete.html
    └── user_auth/
        │-- login.html
        │-- register.html
        │-- profile.html
        └── edit_profile.html
