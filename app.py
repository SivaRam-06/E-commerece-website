import os
import sqlite3
from datetime import datetime
from functools import wraps
from flask import (Flask,flash,g,jsonify,redirect,render_template,request,session,url_for,)
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.path.join(BASE_DIR, "database.db")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "images", "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-change-me-in-production")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    db.executescript(
        """
        PRAGMA foreign_keys = ON;

        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            slug TEXT NOT NULL UNIQUE,
            description TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            full_name TEXT,
            phone TEXT,
            is_admin INTEGER DEFAULT 0,
            theme_pref TEXT DEFAULT 'light',
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            slug TEXT NOT NULL UNIQUE,
            description TEXT,
            price REAL NOT NULL,
            compare_at_price REAL,
            category_id INTEGER NOT NULL REFERENCES categories(id),
            image TEXT,
            stock INTEGER DEFAULT 0,
            is_featured INTEGER DEFAULT 0,
            popularity INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS cart (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
            quantity INTEGER NOT NULL DEFAULT 1,
            UNIQUE(user_id, product_id)
        );

        CREATE TABLE IF NOT EXISTS wishlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
            UNIQUE(user_id, product_id)
        );

        CREATE TABLE IF NOT EXISTS addresses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            label TEXT,
            full_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            line1 TEXT NOT NULL,
            line2 TEXT,
            city TEXT NOT NULL,
            state TEXT NOT NULL,
            zip TEXT NOT NULL,
            country TEXT DEFAULT 'India',
            is_default INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id),
            total REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'Processing',
            payment_method TEXT,
            shipping_snapshot TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
            product_id INTEGER NOT NULL REFERENCES products(id),
            quantity INTEGER NOT NULL,
            price_at_purchase REAL NOT NULL,
            product_name TEXT
        );

        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id),
            product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
            rating INTEGER NOT NULL CHECK(rating >= 1 AND rating <= 5),
            comment TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            UNIQUE(user_id, product_id)
        );

        CREATE INDEX IF NOT EXISTS idx_products_category ON products(category_id);
        CREATE INDEX IF NOT EXISTS idx_products_featured ON products(is_featured);
        CREATE INDEX IF NOT EXISTS idx_cart_user ON cart(user_id);
        CREATE INDEX IF NOT EXISTS idx_orders_user ON orders(user_id);
        """
    )
    db.commit()

    cur = db.execute("SELECT COUNT(*) AS c FROM users WHERE username = 'admin'")
    if cur.fetchone()["c"] == 0:
        db.execute(
            """INSERT INTO users (username, email, password_hash, full_name, is_admin)
               VALUES (?, ?, ?, ?, 1)""",
            (
                "admin",
                "admin@shop.local",
                generate_password_hash("admin123"),
                "Store Admin",
            ),
        )
        db.commit()

    cur = db.execute("SELECT COUNT(*) AS c FROM categories")
    if cur.fetchone()["c"] == 0:
        cats = [
            ("Electronics", "electronics", "Gadgets and tech"),
            ("Fashion", "fashion", "Apparel and accessories"),
            ("Home & Living", "home-living", "Furniture and decor"),
            ("Beauty", "beauty", "Skincare and cosmetics"),
            ("Sports", "sports", "Fitness and outdoors"),
        ]
        for name, slug, desc in cats:
            db.execute(
                "INSERT INTO categories (name, slug, description) VALUES (?, ?, ?)",
                (name, slug, desc),
            )
        db.commit()

    cur = db.execute("SELECT COUNT(*) AS c FROM products")
    if cur.fetchone()["c"] == 0:
        samples = [
            (
                "Nova Wireless Earbuds",
                "nova-wireless-earbuds",
                "ANC, 32h battery, premium sound.",
                4999,
                6999,
                1,
                "uploads/sample-earbuds.jpg",
                120,
                1,
                98,
            ),
            (
                "Apex Smartwatch Pro",
                "apex-smartwatch-pro",
                "AMOLED, GPS, health tracking.",
                12999,
                15999,
                1,
                "uploads/sample-watch.jpg",
                45,
                1,
                120,
            ),
            (
                "Linen Blend Shirt",
                "linen-blend-shirt",
                "Breathable casual fit.",
                1899,
                2499,
                2,
                "uploads/sample-shirt.jpg",
                200,
                1,
                76,
            ),
            (
                "Urban Sneakers",
                "urban-sneakers",
                "Lightweight street style.",
                3499,
                4499,
                2,
                "uploads/sample-sneakers.jpg",
                80,
                1,
                88,
            ),
            (
                "Ceramic Table Lamp",
                "ceramic-table-lamp",
                "Warm ambient lighting.",
                2199,
                None,
                3,
                "uploads/sample-lamp.jpg",
                60,
                0,
                40,
            ),
            (
                "Vitamin C Serum",
                "vitamin-c-serum",
                "Brightening daily serum.",
                899,
                1199,
                4,
                "uploads/sample-serum.jpg",
                150,
                0,
                55,
            ),
            (
                "Yoga Mat Premium",
                "yoga-mat-premium",
                "Non-slip, extra thick.",
                1299,
                1699,
                5,
                "uploads/sample-yoga.jpg",
                90,
                0,
                62,
            ),
            (
                "4K Action Camera",
                "4k-action-camera",
                "Waterproof, stabilization.",
                18999,
                22999,
                1,
                "uploads/sample-camera.jpg",
                25,
                0,
                70,
            ),
        ]
        for row in samples:
            db.execute(
                """INSERT INTO products
                (name, slug, description, price, compare_at_price, category_id,
                 image, stock, is_featured, popularity) VALUES (?,?,?,?,?,?,?,?,?,?)""",
                row,
            )
        db.commit()

    cur = db.execute("SELECT COUNT(*) AS c FROM reviews")
    if cur.fetchone()["c"] == 0:
        admin_row = db.execute(
            "SELECT id FROM users WHERE username = 'admin'"
        ).fetchone()
        uid = admin_row["id"] if admin_row else 1
        pids = [
            r["id"]
            for r in db.execute(
                "SELECT id FROM products ORDER BY id LIMIT 3"
            ).fetchall()
        ]
        demo = [
            (5, "Excellent quality and fast delivery!"),
            (5, "Worth every rupee. Premium feel."),
            (4, "Great fit, will buy again."),
        ]
        for i, pid in enumerate(pids):
            if i < len(demo):
                rating, text = demo[i]
                db.execute(
                    "INSERT INTO reviews (user_id, product_id, rating, comment) VALUES (?,?,?,?)",
                    (uid, pid, rating, text),
                )
        db.commit()

    db.close()


def query_one(sql, args=()):
    return get_db().execute(sql, args).fetchone()


def query_all(sql, args=()):
    return get_db().execute(sql, args).fetchall()


def current_user_id():
    return session.get("user_id")


def login_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if not current_user_id():
            flash("Please sign in to continue.", "warning")
            return redirect(url_for("login", next=request.path))
        return f(*args, **kwargs)

    return wrapped


def admin_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        uid = current_user_id()
        if not uid:
            flash("Admin sign in required.", "warning")
            return redirect(url_for("admin_login"))
        row = query_one("SELECT is_admin FROM users WHERE id = ?", (uid,))
        if not row or not row["is_admin"]:
            flash("Access denied.", "danger")
            return redirect(url_for("index"))
        return f(*args, **kwargs)

    return wrapped


@app.context_processor
def inject_globals():
    uid = current_user_id()
    cart_count = 0
    wish_count = 0
    theme = session.get("theme", "light")
    user_row = None
    if uid:
        c = query_one(
            "SELECT COALESCE(SUM(quantity),0) AS n FROM cart WHERE user_id = ?",
            (uid,),
        )
        cart_count = int(c["n"] or 0)
        w = query_one(
            "SELECT COUNT(*) AS n FROM wishlist WHERE user_id = ?", (uid,)
        )
        wish_count = int(w["n"] or 0)
        user_row = query_one(
            "SELECT id, username, email, full_name, is_admin, theme_pref FROM users WHERE id = ?",
            (uid,),
        )
        if user_row and user_row["theme_pref"]:
            theme = user_row["theme_pref"]
        if user_row is not None:
            user_row = dict(user_row)
    return dict(
        cart_count=cart_count,
        wish_count=wish_count,
        current_user=user_row,
        theme=theme,
        year=datetime.now().year,
    )


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ------------- Public pages -------------


@app.route("/")
def index():
    featured = query_all(
        """SELECT p.*, c.name AS category_name FROM products p
           JOIN categories c ON c.id = p.category_id
           WHERE p.is_featured = 1 ORDER BY p.popularity DESC LIMIT 8"""
    )
    trending = query_all(
        """SELECT p.*, c.name AS category_name FROM products p
           JOIN categories c ON c.id = p.category_id
           ORDER BY p.popularity DESC LIMIT 8"""
    )
    categories = query_all("SELECT * FROM categories ORDER BY name")
    reviews = query_all(
        """SELECT r.*, u.full_name, u.username, p.name AS product_name
           FROM reviews r JOIN users u ON u.id = r.user_id
           JOIN products p ON p.id = r.product_id
           ORDER BY r.created_at DESC LIMIT 12"""
    )
    return render_template(
        "index.html",
        featured=featured,
        trending=trending,
        categories=categories,
        reviews=reviews,
    )


@app.route("/products")
def products():
    search = (request.args.get("q") or "").strip()
    cat_slug = request.args.get("category") or ""
    min_p = request.args.get("min_price", type=float)
    max_p = request.args.get("max_price", type=float)
    sort = request.args.get("sort", "newest")
    page = request.args.get("page", 1, type=int) or 1
    per_page = 9
    where = ["1=1"]
    params = []
    if search:
        where.append("(p.name LIKE ? OR p.description LIKE ?)")
        like = f"%{search}%"
        params.extend([like, like])
    if cat_slug:
        where.append("c.slug = ?")
        params.append(cat_slug)
    if min_p is not None:
        where.append("p.price >= ?")
        params.append(min_p)
    if max_p is not None:
        where.append("p.price <= ?")
        params.append(max_p)
    wh = " AND ".join(where)
    order = "p.created_at DESC"
    if sort == "price_low":
        order = "p.price ASC"
    elif sort == "price_high":
        order = "p.price DESC"
    elif sort == "popularity":
        order = "p.popularity DESC, p.created_at DESC"

    total = query_one(
        f"""SELECT COUNT(*) AS n FROM products p
            JOIN categories c ON c.id = p.category_id WHERE {wh}""",
        params,
    )["n"]
    pages = max(1, (total + per_page - 1) // per_page)
    page = max(1, min(page, pages))
    offset = (page - 1) * per_page

    rows = query_all(
        f"""SELECT p.*, c.name AS category_name, c.slug AS category_slug
            FROM products p JOIN categories c ON c.id = p.category_id
            WHERE {wh} ORDER BY {order} LIMIT ? OFFSET ?""",
        params + [per_page, offset],
    )
    cats = query_all("SELECT * FROM categories ORDER BY name")
    uid = current_user_id()
    wish_ids = set()
    if uid:
        for w in query_all(
            "SELECT product_id FROM wishlist WHERE user_id = ?", (uid,)
        ):
            wish_ids.add(w["product_id"])

    return render_template(
        "products.html",
        products=rows,
        categories=cats,
        search=search,
        cat_slug=cat_slug,
        min_p=min_p,
        max_p=max_p,
        sort=sort,
        page=page,
        pages=pages,
        total=total,
        wish_ids=wish_ids,
    )


@app.route("/product/<int:pid>")
def product_detail(pid):
    p = query_one(
        """SELECT p.*, c.name AS category_name, c.slug AS category_slug
           FROM products p JOIN categories c ON c.id = p.category_id
           WHERE p.id = ?""",
        (pid,),
    )
    if not p:
        flash("Product not found.", "danger")
        return redirect(url_for("products"))
    rel = query_all(
        """SELECT p.*, c.name AS category_name FROM products p
           JOIN categories c ON c.id = p.category_id
           WHERE p.category_id = ? AND p.id != ? ORDER BY p.popularity DESC LIMIT 4""",
        (p["category_id"], pid),
    )
    revs = query_all(
        """SELECT r.*, u.full_name, u.username FROM reviews r
           JOIN users u ON u.id = r.user_id WHERE r.product_id = ?
           ORDER BY r.created_at DESC""",
        (pid,),
    )
    avg = query_one(
        "SELECT AVG(rating) AS a, COUNT(*) AS n FROM reviews WHERE product_id = ?",
        (pid,),
    )
    uid = current_user_id()
    in_wish = False
    if uid:
        in_wish = bool(
            query_one(
                "SELECT 1 FROM wishlist WHERE user_id = ? AND product_id = ?",
                (uid, pid),
            )
        )
    return render_template(
        "product_detail.html",
        product=p,
        related=rel,
        reviews=revs,
        avg_rating=avg["a"] or 0,
        review_count=avg["n"] or 0,
        in_wishlist=in_wish,
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user_id():
        return redirect(url_for("index"))
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        row = query_one(
            "SELECT * FROM users WHERE username = ? OR email = ?",
            (username, username),
        )
        if row and check_password_hash(row["password_hash"], password):
            session["user_id"] = row["id"]
            session["theme"] = row["theme_pref"] or "light"
            flash("Welcome back!", "success")
            nxt = (
                request.form.get("next")
                or request.args.get("next")
                or url_for("index")
            )
            if not isinstance(nxt, str) or not nxt.startswith("/"):
                nxt = url_for("index")
            return redirect(nxt)
        flash("Invalid credentials.", "danger")
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user_id():
        return redirect(url_for("index"))
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        full_name = (request.form.get("full_name") or "").strip()
        if len(username) < 3 or len(password) < 6:
            flash("Username (3+) and password (6+ chars) required.", "warning")
            return render_template("register.html")
        try:
            get_db().execute(
                """INSERT INTO users (username, email, password_hash, full_name)
                   VALUES (?, ?, ?, ?)""",
                (
                    username,
                    email,
                    generate_password_hash(password),
                    full_name or username,
                ),
            )
            get_db().commit()
            flash("Account created. Please sign in.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Username or email already registered.", "danger")
    return render_template("register.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Signed out.", "info")
    return redirect(url_for("index"))


@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = (request.form.get("email") or "").strip()
        row = query_one("SELECT id FROM users WHERE email = ?", (email,))
        if row:
            flash(
                "If that email exists, password reset instructions were sent (demo).",
                "success",
            )
        else:
            flash(
                "If that email exists, password reset instructions were sent (demo).",
                "info",
            )
        return redirect(url_for("login"))
    return render_template("forgot_password.html")


@app.route("/cart")
@login_required
def cart():
    uid = current_user_id()
    rows = query_all(
        """SELECT c.id, c.quantity, p.id AS product_id, p.name, p.price, p.image, p.stock
           FROM cart c JOIN products p ON p.id = c.product_id WHERE c.user_id = ?
           ORDER BY c.id""",
        (uid,),
    )
    total = sum(float(r["price"]) * r["quantity"] for r in rows)
    return render_template("cart.html", items=rows, total=total)


@app.route("/cart/add", methods=["POST"])
@login_required
def cart_add():
    uid = current_user_id()
    pid = request.form.get("product_id", type=int)
    qty = request.form.get("quantity", 1, type=int) or 1
    if not pid:
        flash("Invalid product.", "danger")
        return redirect(url_for("products"))
    p = query_one("SELECT id, stock FROM products WHERE id = ?", (pid,))
    if not p:
        flash("Product not found.", "danger")
        return redirect(url_for("products"))
    qty = max(1, min(qty, p["stock"]))
    ex = query_one(
        "SELECT id, quantity FROM cart WHERE user_id = ? AND product_id = ?",
        (uid, pid),
    )
    if ex:
        new_q = min(ex["quantity"] + qty, p["stock"])
        get_db().execute(
            "UPDATE cart SET quantity = ? WHERE id = ?", (new_q, ex["id"])
        )
    else:
        get_db().execute(
            "INSERT INTO cart (user_id, product_id, quantity) VALUES (?,?,?)",
            (uid, pid, qty),
        )
    get_db().commit()
    flash("Added to cart.", "success")
    action = request.form.get("action") or "cart"
    if action == "checkout":
        red = url_for("checkout")
    else:
        red = request.form.get("redirect") or url_for("cart")
        if not isinstance(red, str) or not red.startswith("/"):
            red = url_for("cart")
    return redirect(red)


@app.route("/cart/update", methods=["POST"])
@login_required
def cart_update():
    uid = current_user_id()
    cid = request.form.get("cart_id", type=int)
    qty = request.form.get("quantity", type=int)
    if not cid or qty is None or qty < 1:
        return redirect(url_for("cart"))
    row = query_one(
        """SELECT c.id, p.stock FROM cart c JOIN products p ON p.id = c.product_id
           WHERE c.id = ? AND c.user_id = ?""",
        (cid, uid),
    )
    if not row:
        return redirect(url_for("cart"))
    qty = min(qty, row["stock"])
    get_db().execute("UPDATE cart SET quantity = ? WHERE id = ?", (qty, cid))
    get_db().commit()
    flash("Cart updated.", "success")
    return redirect(url_for("cart"))


@app.route("/cart/remove/<int:cid>", methods=["POST"])
@login_required
def cart_remove(cid):
    uid = current_user_id()
    get_db().execute("DELETE FROM cart WHERE id = ? AND user_id = ?", (cid, uid))
    get_db().commit()
    flash("Item removed.", "info")
    return redirect(url_for("cart"))


@app.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    uid = current_user_id()
    rows = query_all(
        """SELECT c.id, c.quantity, p.id AS product_id, p.name, p.price, p.image, p.stock
           FROM cart c JOIN products p ON p.id = c.product_id WHERE c.user_id = ?""",
        (uid,),
    )
    if not rows:
        flash("Your cart is empty.", "warning")
        return redirect(url_for("products"))
    total = sum(float(r["price"]) * r["quantity"] for r in rows)
    addresses = query_all(
        "SELECT * FROM addresses WHERE user_id = ? ORDER BY is_default DESC, id DESC",
        (uid,),
    )

    if request.method == "POST":
        payment = request.form.get("payment") or "cod"
        use_saved = request.form.get("address_id", type=int)
        if use_saved:
            addr = query_one(
                "SELECT * FROM addresses WHERE id = ? AND user_id = ?",
                (use_saved, uid),
            )
            if not addr:
                flash("Invalid address.", "danger")
                return redirect(url_for("checkout"))
            snap = (
                f"{addr['full_name']}, {addr['line1']}, {addr.get('line2') or ''}, "
                f"{addr['city']}, {addr['state']} {addr['zip']}, {addr['phone']}"
            )
        else:
            line1 = (request.form.get("line1") or "").strip()
            city = (request.form.get("city") or "").strip()
            if not line1 or not city:
                flash("Please complete shipping fields or pick a saved address.", "danger")
                return redirect(url_for("checkout"))
            snap = " | ".join(
                [
                    request.form.get("full_name", ""),
                    request.form.get("phone", ""),
                    line1,
                    request.form.get("line2", ""),
                    city,
                    request.form.get("state", ""),
                    request.form.get("zip", ""),
                ]
            )
        db = get_db()
        cur = db.execute(
            "INSERT INTO orders (user_id, total, status, payment_method, shipping_snapshot) VALUES (?,?,?,?,?)",
            (uid, total, "Processing", payment, snap),
        )
        oid = cur.lastrowid
        for r in rows:
            db.execute(
                """INSERT INTO order_items (order_id, product_id, quantity, price_at_purchase, product_name)
                   VALUES (?,?,?,?,?)""",
                (oid, r["product_id"], r["quantity"], float(r["price"]), r["name"]),
            )
            db.execute(
                "UPDATE products SET stock = stock - ? WHERE id = ?",
                (r["quantity"], r["product_id"]),
            )
        db.execute("DELETE FROM cart WHERE user_id = ?", (uid,))
        db.commit()
        flash("Order placed successfully!", "success")
        return redirect(url_for("orders"))

    return render_template(
        "checkout.html", items=rows, total=total, addresses=addresses
    )


@app.route("/orders")
@login_required
def orders():
    uid = current_user_id()
    rows = query_all(
        "SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC", (uid,)
    )
    return render_template("orders.html", orders=rows)


@app.route("/order/<int:oid>")
@login_required
def order_detail(oid):
    uid = current_user_id()
    o = query_one("SELECT * FROM orders WHERE id = ? AND user_id = ?", (oid, uid))
    if not o:
        flash("Order not found.", "danger")
        return redirect(url_for("orders"))
    items = query_all(
        "SELECT * FROM order_items WHERE order_id = ?", (oid,)
    )
    return render_template("order_detail.html", order=o, items=items)


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    uid = current_user_id()
    user = query_one("SELECT * FROM users WHERE id = ?", (uid,))
    if request.method == "POST":
        action = request.form.get("action")
        if action == "profile":
            full_name = (request.form.get("full_name") or "").strip()
            phone = (request.form.get("phone") or "").strip()
            email = (request.form.get("email") or "").strip().lower()
            try:
                get_db().execute(
                    "UPDATE users SET full_name = ?, phone = ?, email = ? WHERE id = ?",
                    (full_name, phone, email, uid),
                )
                get_db().commit()
                flash("Profile updated.", "success")
            except sqlite3.IntegrityError:
                flash("Email already in use.", "danger")
        elif action == "password":
            old = request.form.get("old_password") or ""
            new = request.form.get("new_password") or ""
            if not check_password_hash(user["password_hash"], old):
                flash("Current password incorrect.", "danger")
            elif len(new) < 6:
                flash("New password too short.", "warning")
            else:
                get_db().execute(
                    "UPDATE users SET password_hash = ? WHERE id = ?",
                    (generate_password_hash(new), uid),
                )
                get_db().commit()
                flash("Password changed.", "success")
        elif action == "address":
            db = get_db()
            cur = db.execute(
                """INSERT INTO addresses
                (user_id, label, full_name, phone, line1, line2, city, state, zip, country, is_default)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    uid,
                    (request.form.get("label") or "Home").strip(),
                    request.form.get("addr_name", "").strip(),
                    request.form.get("addr_phone", "").strip(),
                    request.form.get("line1", "").strip(),
                    (request.form.get("line2") or "").strip(),
                    request.form.get("city", "").strip(),
                    request.form.get("state", "").strip(),
                    request.form.get("zip", "").strip(),
                    (request.form.get("country") or "India").strip(),
                    1 if request.form.get("is_default") else 0,
                ),
            )
            aid = cur.lastrowid
            if request.form.get("is_default"):
                db.execute(
                    "UPDATE addresses SET is_default = 0 WHERE user_id = ? AND id != ?",
                    (uid, aid),
                )
            db.commit()
            flash("Address saved.", "success")
        return redirect(url_for("profile"))

    addresses = query_all(
        "SELECT * FROM addresses WHERE user_id = ? ORDER BY is_default DESC, id DESC",
        (uid,),
    )
    return render_template("profile.html", user=user, addresses=addresses)


@app.route("/newsletter", methods=["POST"])
def newsletter():
    flash("Thanks for subscribing!", "success")
    return redirect(request.referrer or url_for("index"))


@app.route("/theme", methods=["POST"])
def set_theme():
    mode = request.form.get("theme", "light")
    if mode not in ("light", "dark"):
        mode = "light"
    session["theme"] = mode
    if current_user_id():
        get_db().execute(
            "UPDATE users SET theme_pref = ? WHERE id = ?", (mode, current_user_id())
        )
        get_db().commit()
    return redirect(request.referrer or url_for("index"))


@app.route("/wishlist")
@login_required
def wishlist_page():
    uid = current_user_id()
    rows = query_all(
        """SELECT p.*, c.name AS category_name FROM products p
           JOIN categories c ON c.id = p.category_id
           JOIN wishlist w ON w.product_id = p.id
           WHERE w.user_id = ? ORDER BY w.id DESC""",
        (uid,),
    )
    return render_template("wishlist.html", products=rows)


@app.route("/wishlist/toggle/<int:pid>", methods=["POST"])
@login_required
def wishlist_toggle(pid):
    uid = current_user_id()
    if not query_one("SELECT id FROM products WHERE id = ?", (pid,)):
        return jsonify(ok=False), 404
    ex = query_one(
        "SELECT id FROM wishlist WHERE user_id = ? AND product_id = ?",
        (uid, pid),
    )
    if ex:
        get_db().execute("DELETE FROM wishlist WHERE id = ?", (ex["id"],))
        get_db().commit()
        return jsonify(ok=True, in_wishlist=False)
    get_db().execute(
        "INSERT INTO wishlist (user_id, product_id) VALUES (?,?)", (uid, pid)
    )
    get_db().commit()
    return jsonify(ok=True, in_wishlist=True)


@app.route("/api/product/<int:pid>/quick")
def api_quick_view(pid):
    p = query_one(
        """SELECT p.*, c.name AS category_name FROM products p
           JOIN categories c ON c.id = p.category_id WHERE p.id = ?""",
        (pid,),
    )
    if not p:
        return jsonify(error="not found"), 404
    d = dict(p)
    for k in d:
        if isinstance(d[k], bytes):
            d[k] = d[k].decode()
    return jsonify(d)


@app.route("/review/<int:pid>", methods=["POST"])
@login_required
def add_review(pid):
    uid = current_user_id()
    if not query_one("SELECT id FROM products WHERE id = ?", (pid,)):
        flash("Invalid product.", "danger")
        return redirect(url_for("products"))
    rating = request.form.get("rating", type=int) or 5
    rating = max(1, min(5, rating))
    comment = (request.form.get("comment") or "").strip()
    try:
        get_db().execute(
            "INSERT INTO reviews (user_id, product_id, rating, comment) VALUES (?,?,?,?)",
            (uid, pid, rating, comment),
        )
        get_db().execute(
            "UPDATE products SET popularity = popularity + ? WHERE id = ?",
            (rating, pid),
        )
        get_db().commit()
        flash("Thank you for your review!", "success")
    except sqlite3.IntegrityError:
        flash("You already reviewed this product.", "warning")
    return redirect(url_for("product_detail", pid=pid))


# ------------- Admin -------------


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        row = query_one(
            "SELECT * FROM users WHERE (username = ? OR email = ?) AND is_admin = 1",
            (username, username),
        )
        if row and check_password_hash(row["password_hash"], password):
            session["user_id"] = row["id"]
            flash("Admin access granted.", "success")
            return redirect(url_for("admin_dashboard"))
        flash("Invalid admin credentials.", "danger")
    return render_template("admin/login.html")


@app.route("/admin")
@admin_required
def admin_dashboard():
    stats = {
        "users": query_one("SELECT COUNT(*) AS n FROM users WHERE is_admin = 0")[
            "n"
        ],
        "products": query_one("SELECT COUNT(*) AS n FROM products")["n"],
        "orders": query_one("SELECT COUNT(*) AS n FROM orders")["n"],
        "revenue": query_one("SELECT COALESCE(SUM(total),0) AS s FROM orders")["s"],
    }
    recent = query_all(
        """SELECT o.*, u.username FROM orders o
           JOIN users u ON u.id = o.user_id ORDER BY o.created_at DESC LIMIT 8"""
    )
    return render_template("admin/dashboard.html", stats=stats, recent_orders=recent)


@app.route("/admin/products")
@admin_required
def admin_products():
    rows = query_all(
        """SELECT p.*, c.name AS cat FROM products p
           JOIN categories c ON c.id = p.category_id ORDER BY p.id DESC"""
    )
    return render_template("admin/products.html", products=rows)


@app.route("/admin/products/new", methods=["GET", "POST"])
@app.route("/admin/products/<int:pid>/edit", methods=["GET", "POST"])
@admin_required
def admin_product_form(pid=None):
    cats = query_all("SELECT * FROM categories ORDER BY name")
    row = None
    if pid:
        row = query_one("SELECT * FROM products WHERE id = ?", (pid,))
        if not row:
            flash("Product not found.", "danger")
            return redirect(url_for("admin_products"))
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        slug = request.form.get("slug", "").strip().lower().replace(" ", "-")
        desc = request.form.get("description", "")
        price = float(request.form.get("price") or 0)
        cap = request.form.get("compare_at_price")
        compare_at = float(cap) if cap else None
        category_id = request.form.get("category_id", type=int)
        stock = request.form.get("stock", type=int) or 0
        is_featured = 1 if request.form.get("is_featured") else 0
        popularity = request.form.get("popularity", type=int) or 0
        image = row["image"] if row else "placeholder.svg"
        f = request.files.get("image")
        if f and f.filename and allowed_file(f.filename):
            fn = secure_filename(f.filename)
            path = f"uploads/{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{fn}"
            full = os.path.join(BASE_DIR, "static", "images", path)
            f.save(full)
            image = path
        db = get_db()
        try:
            if pid:
                db.execute(
                    """UPDATE products SET name=?, slug=?, description=?, price=?,
                       compare_at_price=?, category_id=?, image=?, stock=?, is_featured=?, popularity=?
                       WHERE id=?""",
                    (
                        name,
                        slug,
                        desc,
                        price,
                        compare_at,
                        category_id,
                        image,
                        stock,
                        is_featured,
                        popularity,
                        pid,
                    ),
                )
                flash("Product updated.", "success")
            else:
                db.execute(
                    """INSERT INTO products
                    (name, slug, description, price, compare_at_price, category_id, image, stock, is_featured, popularity)
                    VALUES (?,?,?,?,?,?,?,?,?,?)""",
                    (
                        name,
                        slug,
                        desc,
                        price,
                        compare_at,
                        category_id,
                        image,
                        stock,
                        is_featured,
                        popularity,
                    ),
                )
                flash("Product created.", "success")
            db.commit()
            return redirect(url_for("admin_products"))
        except sqlite3.IntegrityError:
            flash("Slug must be unique.", "danger")
    return render_template("admin/product_form.html", product=row, categories=cats)


@app.route("/admin/products/<int:pid>/delete", methods=["POST"])
@admin_required
def admin_product_delete(pid):
    get_db().execute("DELETE FROM products WHERE id = ?", (pid,))
    get_db().commit()
    flash("Product deleted.", "info")
    return redirect(url_for("admin_products"))


@app.route("/admin/categories")
@admin_required
def admin_categories():
    rows = query_all("SELECT * FROM categories ORDER BY name")
    return render_template("admin/categories.html", categories=rows)


@app.route("/admin/categories/new", methods=["GET", "POST"])
@app.route("/admin/categories/<int:cid>/edit", methods=["GET", "POST"])
@admin_required
def admin_category_form(cid=None):
    row = query_one("SELECT * FROM categories WHERE id = ?", (cid,)) if cid else None
    if cid and not row:
        flash("Category not found.", "danger")
        return redirect(url_for("admin_categories"))
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        slug = request.form.get("slug", "").strip().lower().replace(" ", "-")
        desc = request.form.get("description", "")
        try:
            if cid:
                get_db().execute(
                    "UPDATE categories SET name=?, slug=?, description=? WHERE id=?",
                    (name, slug, desc, cid),
                )
                flash("Category updated.", "success")
            else:
                get_db().execute(
                    "INSERT INTO categories (name, slug, description) VALUES (?,?,?)",
                    (name, slug, desc),
                )
                flash("Category created.", "success")
            get_db().commit()
            return redirect(url_for("admin_categories"))
        except sqlite3.IntegrityError:
            flash("Name or slug must be unique.", "danger")
    return render_template("admin/category_form.html", category=row)


@app.route("/admin/categories/<int:cid>/delete", methods=["POST"])
@admin_required
def admin_category_delete(cid):
    cnt = query_one(
        "SELECT COUNT(*) AS n FROM products WHERE category_id = ?", (cid,)
    )["n"]
    if cnt:
        flash("Cannot delete category with products.", "warning")
    else:
        get_db().execute("DELETE FROM categories WHERE id = ?", (cid,))
        get_db().commit()
        flash("Category deleted.", "info")
    return redirect(url_for("admin_categories"))


@app.route("/admin/users")
@admin_required
def admin_users():
    rows = query_all(
        "SELECT id, username, email, full_name, is_admin, created_at FROM users ORDER BY id DESC"
    )
    return render_template("admin/users.html", users=rows)


@app.route("/admin/orders")
@admin_required
def admin_orders():
    rows = query_all(
        """SELECT o.*, u.username FROM orders o
           JOIN users u ON u.id = o.user_id ORDER BY o.created_at DESC"""
    )
    return render_template("admin/admin_orders.html", orders=rows)


@app.route("/admin/orders/<int:oid>/status", methods=["POST"])
@admin_required
def admin_order_status(oid):
    status = request.form.get("status") or "Processing"
    allowed = ("Processing", "Shipped", "Out for delivery", "Delivered", "Cancelled")
    if status not in allowed:
        status = "Processing"
    get_db().execute("UPDATE orders SET status = ? WHERE id = ?", (status, oid))
    get_db().commit()
    flash("Order status updated.", "success")
    return redirect(url_for("admin_orders"))


if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="0.0.0.0", port=5000)
