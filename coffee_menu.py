from __future__ import annotations

import csv
import os
import random
import tkinter as tk
from dataclasses import dataclass, field
from datetime import datetime
from tkinter import messagebox, ttk
from typing import Dict, List, Optional

from PIL import Image, ImageDraw, ImageFont, ImageTk


# -----------------------------------------------------------------------------
# Configuration & Constants
# -----------------------------------------------------------------------------

APP_TITLE = "Code & Coffee — Digital Menu"
CURRENCY = "₹"            # INR
TAX_RATE = 0.05           # 5% tax

RECEIPTS_DIR = "receipts"
ORDERS_CSV = "orders.csv"

COLORS = {
    "bg":            "#1B1410",
    "panel":         "#241B16",
    "panel_alt":     "#2E231C",
    "card":          "#33271F",
    "accent":        "#D4A574",
    "accent_dark":   "#A77B4F",
    "text":          "#F2E8DC",
    "text_dim":      "#B9A99A",
    "danger":        "#E0654A",
    "ok":            "#7BB369",
    "border":        "#4A3A2E",
}

FONT_FAMILY = "Segoe UI"


# -----------------------------------------------------------------------------
# Sample Menu Data  (BUG FIX: "desc" → "description" throughout)
# -----------------------------------------------------------------------------

MENU_DATA: List[Dict] = [
    # ---------- Coffee ----------
    {"name": "Espresso",          "price": 120, "category": "Coffee",
     "description": "A bold, concentrated shot of pure arabica perfection.",
     "color": "#6F4E37"},
    {"name": "Cappuccino",        "price": 180, "category": "Coffee",
     "description": "Equal parts espresso, steamed milk, and silky foam.",
     "color": "#A67B5B"},
    {"name": "Caffe Latte",       "price": 200, "category": "Coffee",
     "description": "Smooth espresso with velvety steamed milk and light foam.",
     "color": "#C19A6B"},
    {"name": "Mocha",             "price": 220, "category": "Coffee",
     "description": "Espresso, chocolate, and steamed milk — pure indulgence.",
     "color": "#4B2E2A"},
    {"name": "Americano",         "price": 150, "category": "Coffee",
     "description": "Espresso diluted with hot water for a clean, bold cup.",
     "color": "#3B2417"},

    # ---------- Tea ----------
    {"name": "Masala Chai",       "price": 90,  "category": "Tea",
     "description": "Classic Indian spiced milk tea, brewed strong and aromatic.",
     "color": "#C68E5F"},
    {"name": "Green Tea",         "price": 100, "category": "Tea",
     "description": "Light, refreshing, and full of antioxidants.",
     "color": "#7A9F60"},
    {"name": "Earl Grey",         "price": 130, "category": "Tea",
     "description": "Black tea infused with the citrus aroma of bergamot.",
     "color": "#6B4423"},
    {"name": "Lemon Honey Tea",   "price": 110, "category": "Tea",
     "description": "Soothing herbal blend with fresh lemon and pure honey.",
     "color": "#E1B84B"},

    # ---------- Cold Beverages ----------
    {"name": "Iced Coffee",       "price": 180, "category": "Cold Beverages",
     "description": "Chilled black coffee over ice — simple and refreshing.",
     "color": "#3E2C20"},
    {"name": "Cold Brew",         "price": 220, "category": "Cold Beverages",
     "description": "12-hour slow-steeped coffee. Smooth, low acidity.",
     "color": "#2A1B12"},
    {"name": "Iced Latte",        "price": 230, "category": "Cold Beverages",
     "description": "Espresso, cold milk, and ice — creamy and refreshing.",
     "color": "#D7B79A"},
    {"name": "Frappe",            "price": 260, "category": "Cold Beverages",
     "description": "Blended iced coffee with whipped cream and chocolate drizzle.",
     "color": "#8C5E3C"},
    {"name": "Fresh Lemonade",    "price": 140, "category": "Cold Beverages",
     "description": "Hand-squeezed lemons, a hint of mint, and sparkling water.",
     "color": "#F2D24B"},

    # ---------- Snacks ----------
    {"name": "Veg Sandwich",      "price": 160, "category": "Snacks",
     "description": "Grilled multigrain with garden veggies and herbed mayo.",
     "color": "#C8A165"},
    {"name": "Paneer Wrap",       "price": 200, "category": "Snacks",
     "description": "Tandoori paneer rolled in soft tortilla with mint chutney.",
     "color": "#E07B4A"},
    {"name": "Croissant",         "price": 130, "category": "Snacks",
     "description": "Buttery, flaky French pastry baked fresh every morning.",
     "color": "#E1B07E"},
    {"name": "Cheese Garlic Bread", "price": 180, "category": "Snacks",
     "description": "Toasted bread loaded with mozzarella, garlic, and herbs.",
     "color": "#D4A45A"},

    # ---------- Desserts ----------
    {"name": "Chocolate Brownie", "price": 170, "category": "Desserts",
     "description": "Warm fudgy brownie served with a scoop of vanilla ice cream.",
     "color": "#3D2418"},
    {"name": "Tiramisu",          "price": 240, "category": "Desserts",
     "description": "Italian classic — coffee-soaked sponge with mascarpone cream.",
     "color": "#A77752"},
    {"name": "Cheesecake",        "price": 220, "category": "Desserts",
     "description": "Creamy New York style cheesecake with a buttery biscuit base.",
     "color": "#F0D9A8"},
    {"name": "Red Velvet Pastry", "price": 200, "category": "Desserts",
     "description": "Soft red velvet sponge layered with cream cheese frosting.",
     "color": "#B23A48"},
]


# -----------------------------------------------------------------------------
# Domain models
# -----------------------------------------------------------------------------

@dataclass
class MenuItem:
    """A single product on the menu."""
    name: str
    price: float
    description: str
    category: str
    color: str

    @property
    def item_id(self) -> str:
        return self.name.lower().replace(" ", "_")


@dataclass
class CartLine:
    """A line in the cart: one menu item with a quantity."""
    item: MenuItem
    quantity: int = 1

    @property
    def line_total(self) -> float:
        return self.item.price * self.quantity


@dataclass
class Cart:
    """The shopping cart."""
    lines: Dict[str, CartLine] = field(default_factory=dict)

    def add(self, item: MenuItem, qty: int = 1) -> None:
        if item.item_id in self.lines:
            self.lines[item.item_id].quantity += qty
        else:
            self.lines[item.item_id] = CartLine(item=item, quantity=qty)

    def increase(self, item_id: str) -> None:
        if item_id in self.lines:
            self.lines[item_id].quantity += 1

    def decrease(self, item_id: str) -> None:
        if item_id in self.lines:
            self.lines[item_id].quantity -= 1
            if self.lines[item_id].quantity <= 0:
                del self.lines[item_id]

    def remove(self, item_id: str) -> None:
        self.lines.pop(item_id, None)

    def clear(self) -> None:
        self.lines.clear()

    @property
    def subtotal(self) -> float:
        return sum(line.line_total for line in self.lines.values())

    @property
    def tax(self) -> float:
        return round(self.subtotal * TAX_RATE, 2)

    @property
    def grand_total(self) -> float:
        return round(self.subtotal + self.tax, 2)

    @property
    def is_empty(self) -> bool:
        return len(self.lines) == 0


# -----------------------------------------------------------------------------
# Placeholder Image Generation
# -----------------------------------------------------------------------------

class PlaceholderImageFactory:
    def __init__(self, size: int = 110) -> None:
        self.size = size
        self._cache: Dict[str, ImageTk.PhotoImage] = {}

    def _initials(self, name: str) -> str:
        words = [w for w in name.split() if w]
        if not words:
            return "?"
        if len(words) == 1:
            return words[0][:2].upper()
        return (words[0][0] + words[1][0]).upper()

    def for_item(self, item: MenuItem) -> ImageTk.PhotoImage:
        if item.item_id in self._cache:
            return self._cache[item.item_id]

        s = self.size
        img = Image.new("RGB", (s, s), item.color)
        draw = ImageDraw.Draw(img)

        for i in range(s):
            alpha = int(40 * (1 - i / s))
            draw.line([(0, i), (i, 0)], fill=self._lighten(item.color, alpha))

        draw.rectangle([(0, 0), (s - 1, s - 1)],
                       outline=self._lighten(item.color, 60), width=2)

        text = self._initials(item.name)
        font = self._load_font(int(s * 0.42))
        bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text(((s - tw) / 2 - bbox[0], (s - th) / 2 - bbox[1]),
                  text, fill="white", font=font)

        tk_img = ImageTk.PhotoImage(img)
        self._cache[item.item_id] = tk_img
        return tk_img

    @staticmethod
    def _lighten(hex_color: str, amount: int) -> tuple:
        h = hex_color.lstrip("#")
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        return (min(255, r + amount), min(255, g + amount), min(255, b + amount))

    @staticmethod
    def _load_font(size: int) -> ImageFont.ImageFont:
        for candidate in ("arial.ttf", "Arial.ttf", "DejaVuSans-Bold.ttf",
                          "DejaVuSans.ttf"):
            try:
                return ImageFont.truetype(candidate, size)
            except (OSError, IOError):
                continue
        return ImageFont.load_default()


# -----------------------------------------------------------------------------
# Order persistence
# -----------------------------------------------------------------------------

class OrderWriter:
    def __init__(self, receipts_dir: str = RECEIPTS_DIR,
                 csv_path: str = ORDERS_CSV) -> None:
        self.receipts_dir = receipts_dir
        self.csv_path = csv_path
        os.makedirs(self.receipts_dir, exist_ok=True)

    @staticmethod
    def _new_order_id() -> str:
        ts = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"CC{ts}{random.randint(100, 999)}"

    def save(self, cart: Cart, customer_name: str = "Guest") -> Dict:
        order_id = self._new_order_id()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        receipt_text = self._format_receipt(order_id, timestamp, cart, customer_name)
        receipt_path = os.path.join(self.receipts_dir, f"{order_id}.txt")
        with open(receipt_path, "w", encoding="utf-8") as fh:
            fh.write(receipt_text)

        self._append_csv(order_id, timestamp, cart, customer_name)

        return {
            "order_id": order_id,
            "timestamp": timestamp,
            "receipt_path": receipt_path,
            "receipt_text": receipt_text,
        }

    def _format_receipt(self, order_id: str, ts: str,
                        cart: Cart, customer: str) -> str:
        line = "-" * 48
        out = []
        out.append(line)
        out.append("           CODE & COFFEE")
        out.append("       The Developer's Cafe")
        out.append(line)
        out.append(f"Order ID : {order_id}")
        out.append(f"Date     : {ts}")
        out.append(f"Customer : {customer}")
        out.append(line)
        out.append(f"{'Item':<22}{'Qty':>4}{'Price':>10}{'Total':>10}")
        out.append(line)
        for cl in cart.lines.values():
            name = cl.item.name
            if len(name) > 22:
                name = name[:21] + "…"
            out.append(
                f"{name:<22}{cl.quantity:>4}"
                f"{CURRENCY}{cl.item.price:>8.2f}"
                f"{CURRENCY}{cl.line_total:>8.2f}"
            )
        out.append(line)
        out.append(f"{'Subtotal':<36}{CURRENCY}{cart.subtotal:>10.2f}")
        out.append(f"{'Tax (5%)':<36}{CURRENCY}{cart.tax:>10.2f}")
        out.append(f"{'GRAND TOTAL':<36}{CURRENCY}{cart.grand_total:>10.2f}")
        out.append(line)
        out.append("    Thank you for visiting Code & Coffee!")
        out.append("        Brewed with ❤  and clean code.")
        out.append(line)
        return "\n".join(out)

    def _append_csv(self, order_id: str, ts: str,
                    cart: Cart, customer: str) -> None:
        write_header = not os.path.exists(self.csv_path)
        with open(self.csv_path, "a", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            if write_header:
                writer.writerow([
                    "order_id", "timestamp", "customer", "item",
                    "category", "unit_price", "quantity", "line_total",
                    "subtotal", "tax", "grand_total",
                ])
            for cl in cart.lines.values():
                writer.writerow([
                    order_id, ts, customer, cl.item.name, cl.item.category,
                    f"{cl.item.price:.2f}", cl.quantity,
                    f"{cl.line_total:.2f}",
                    f"{cart.subtotal:.2f}", f"{cart.tax:.2f}",
                    f"{cart.grand_total:.2f}",
                ])


# -----------------------------------------------------------------------------
# UI Components
# -----------------------------------------------------------------------------

class MenuItemCard(ttk.Frame):
    def __init__(self, parent, item: MenuItem,
                 image_factory: PlaceholderImageFactory,
                 on_add) -> None:
        super().__init__(parent, style="Card.TFrame", padding=12)
        self.item = item
        self.on_add = on_add

        self._photo = image_factory.for_item(item)
        img_lbl = ttk.Label(self, image=self._photo, style="Card.TLabel")
        img_lbl.grid(row=0, column=0, rowspan=3, padx=(0, 12), sticky="n")

        ttk.Label(self, text=item.name, style="CardTitle.TLabel"
                  ).grid(row=0, column=1, sticky="w")

        ttk.Label(self,
                  text=f"{CURRENCY}{item.price:.2f}",
                  style="CardPrice.TLabel"
                  ).grid(row=0, column=2, sticky="e", padx=(8, 0))

        ttk.Label(self,
                  text=item.description,
                  style="CardDesc.TLabel",
                  wraplength=320,
                  justify="left"
                  ).grid(row=1, column=1, columnspan=2, sticky="w", pady=(4, 8))

        add_btn = ttk.Button(self, text="+  Add to Cart",
                             style="Accent.TButton",
                             command=lambda: self.on_add(self.item))
        add_btn.grid(row=2, column=1, columnspan=2, sticky="ew")

        self.columnconfigure(1, weight=1)


class CartLineRow(ttk.Frame):
    def __init__(self, parent, line: CartLine,
                 on_inc, on_dec, on_remove) -> None:
        super().__init__(parent, style="CartRow.TFrame", padding=(10, 8))
        self.line = line

        ttk.Label(self, text=line.item.name,
                  style="CartItem.TLabel"
                  ).grid(row=0, column=0, columnspan=4, sticky="w")
        ttk.Label(self,
                  text=f"{CURRENCY}{line.item.price:.2f} each",
                  style="CartItemDim.TLabel"
                  ).grid(row=1, column=0, columnspan=4, sticky="w", pady=(0, 6))

        ttk.Button(self, text="−", width=3, style="QtyBtn.TButton",
                   command=lambda: on_dec(line.item.item_id)
                   ).grid(row=2, column=0)
        ttk.Label(self, text=str(line.quantity), width=4,
                  anchor="center", style="QtyLabel.TLabel"
                  ).grid(row=2, column=1)
        ttk.Button(self, text="+", width=3, style="QtyBtn.TButton",
                   command=lambda: on_inc(line.item.item_id)
                   ).grid(row=2, column=2)

        ttk.Label(self,
                  text=f"{CURRENCY}{line.line_total:.2f}",
                  style="CartTotal.TLabel"
                  ).grid(row=2, column=3, sticky="e", padx=(12, 8))

        ttk.Button(self, text="✕", width=3, style="Danger.TButton",
                   command=lambda: on_remove(line.item.item_id)
                   ).grid(row=2, column=4, padx=(4, 0))

        self.columnconfigure(3, weight=1)


# -----------------------------------------------------------------------------
# Main Application
# -----------------------------------------------------------------------------

class CoffeeMenuApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1280x800")
        self.minsize(1100, 700)
        self.configure(bg=COLORS["bg"])

        self.menu: List[MenuItem] = [MenuItem(**d) for d in MENU_DATA]
        self.cart = Cart()
        self.image_factory = PlaceholderImageFactory(size=96)
        self.order_writer = OrderWriter()
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._render_menu())

        self._init_styles()
        self._build_layout()
        self._render_menu()
        self._render_cart()

    def _init_styles(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        c = COLORS
        f = FONT_FAMILY

        style.configure(".", background=c["bg"], foreground=c["text"],
                        font=(f, 11))

        style.configure("App.TFrame", background=c["bg"])
        style.configure("Panel.TFrame", background=c["panel"])
        style.configure("PanelAlt.TFrame", background=c["panel_alt"])
        style.configure("Card.TFrame", background=c["card"], relief="flat")
        style.configure("CartRow.TFrame", background=c["panel_alt"])

        style.configure("Header.TLabel", background=c["bg"],
                        foreground=c["accent"], font=(f, 26, "bold"))
        style.configure("SubHeader.TLabel", background=c["bg"],
                        foreground=c["text_dim"], font=(f, 12, "italic"))
        style.configure("SectionTitle.TLabel", background=c["panel"],
                        foreground=c["accent"], font=(f, 14, "bold"))
        style.configure("Card.TLabel", background=c["card"],
                        foreground=c["text"])
        style.configure("CardTitle.TLabel", background=c["card"],
                        foreground=c["text"], font=(f, 13, "bold"))
        style.configure("CardPrice.TLabel", background=c["card"],
                        foreground=c["accent"], font=(f, 13, "bold"))
        style.configure("CardDesc.TLabel", background=c["card"],
                        foreground=c["text_dim"], font=(f, 10))

        style.configure("CartItem.TLabel", background=c["panel_alt"],
                        foreground=c["text"], font=(f, 11, "bold"))
        style.configure("CartItemDim.TLabel", background=c["panel_alt"],
                        foreground=c["text_dim"], font=(f, 9))
        style.configure("CartTotal.TLabel", background=c["panel_alt"],
                        foreground=c["accent"], font=(f, 11, "bold"))
        style.configure("QtyLabel.TLabel", background=c["panel_alt"],
                        foreground=c["text"], font=(f, 11, "bold"))

        style.configure("TotalsLine.TLabel", background=c["panel"],
                        foreground=c["text"], font=(f, 11))
        style.configure("TotalsValue.TLabel", background=c["panel"],
                        foreground=c["text"], font=(f, 11, "bold"))
        style.configure("Grand.TLabel", background=c["panel"],
                        foreground=c["accent"], font=(f, 16, "bold"))

        style.configure("Empty.TLabel", background=c["panel_alt"],
                        foreground=c["text_dim"], font=(f, 11, "italic"))

        style.configure("TNotebook", background=c["bg"], borderwidth=0)
        style.configure("TNotebook.Tab",
                        background=c["panel"],
                        foreground=c["text_dim"],
                        padding=(18, 10),
                        font=(f, 11, "bold"))
        style.map("TNotebook.Tab",
                  background=[("selected", c["accent"])],
                  foreground=[("selected", c["bg"])])

        style.configure("Accent.TButton",
                        background=c["accent"], foreground=c["bg"],
                        font=(f, 11, "bold"), padding=(10, 6), borderwidth=0)
        style.map("Accent.TButton",
                  background=[("active", c["accent_dark"])])

        style.configure("Big.TButton",
                        background=c["accent"], foreground=c["bg"],
                        font=(f, 13, "bold"), padding=(12, 10), borderwidth=0)
        style.map("Big.TButton",
                  background=[("active", c["accent_dark"])])

        style.configure("Ghost.TButton",
                        background=c["panel_alt"], foreground=c["text"],
                        font=(f, 10), padding=(8, 6), borderwidth=0)
        style.map("Ghost.TButton",
                  background=[("active", c["card"])])

        style.configure("Danger.TButton",
                        background=c["danger"], foreground="white",
                        font=(f, 10, "bold"), padding=(2, 2), borderwidth=0)
        style.map("Danger.TButton",
                  background=[("active", "#B84A36")])

        style.configure("QtyBtn.TButton",
                        background=c["card"], foreground=c["text"],
                        font=(f, 11, "bold"), padding=(2, 2), borderwidth=0)
        style.map("QtyBtn.TButton",
                  background=[("active", c["accent_dark"])])

        style.configure("Search.TEntry",
                        fieldbackground=c["panel_alt"],
                        foreground=c["text"],
                        insertcolor=c["text"],
                        bordercolor=c["border"],
                        lightcolor=c["border"],
                        darkcolor=c["border"],
                        padding=8)

    def _build_layout(self) -> None:
        header = ttk.Frame(self, style="App.TFrame", padding=(24, 18))
        header.pack(fill="x")

        logo_img = self._build_logo_image()
        self._logo_ref = logo_img
        ttk.Label(header, image=logo_img, style="App.TFrame"
                  ).grid(row=0, column=0, rowspan=2, padx=(0, 16))

        ttk.Label(header, text="Code & Coffee",
                  style="Header.TLabel"
                  ).grid(row=0, column=1, sticky="sw")
        ttk.Label(header,
                  text="The Developer's Cafe  ·  Brewed with clean code.",
                  style="SubHeader.TLabel"
                  ).grid(row=1, column=1, sticky="nw")

        search_box = ttk.Frame(header, style="App.TFrame")
        search_box.grid(row=0, column=2, rowspan=2, sticky="e")
        header.columnconfigure(2, weight=1)

        ttk.Label(search_box, text="🔎 ", background=COLORS["bg"],
                  foreground=COLORS["text_dim"],
                  font=(FONT_FAMILY, 13)).pack(side="left")
        entry = ttk.Entry(search_box, textvariable=self.search_var,
                          width=32, style="Search.TEntry",
                          font=(FONT_FAMILY, 11))
        entry.pack(side="left")
        self._install_placeholder(entry, "Search menu items…")

        body = ttk.Frame(self, style="App.TFrame", padding=(20, 4, 20, 20))
        body.pack(fill="both", expand=True)
        body.columnconfigure(0, weight=3)
        body.columnconfigure(1, weight=2, minsize=380)
        body.rowconfigure(0, weight=1)

        self.notebook = ttk.Notebook(body)
        self.notebook.grid(row=0, column=0, sticky="nsew", padx=(0, 14))

        self.category_frames: Dict[str, ttk.Frame] = {}
        for category in self._categories():
            tab = ttk.Frame(self.notebook, style="Panel.TFrame")
            self.notebook.add(tab, text=f"  {category}  ")
            scroll = self._make_scrollable(tab)
            self.category_frames[category] = scroll

        self._build_cart_panel(body)

    def _build_cart_panel(self, parent) -> None:
        panel = ttk.Frame(parent, style="Panel.TFrame", padding=18)
        panel.grid(row=0, column=1, sticky="nsew")
        panel.columnconfigure(0, weight=1)
        panel.rowconfigure(2, weight=1)

        ttk.Label(panel, text="🛒  Your Order",
                  style="SectionTitle.TLabel"
                  ).grid(row=0, column=0, sticky="w")

        ttk.Separator(panel, orient="horizontal").grid(
            row=1, column=0, sticky="ew", pady=(8, 8))

        self.cart_container = ttk.Frame(panel, style="Panel.TFrame")
        self.cart_container.grid(row=2, column=0, sticky="nsew")
        self.cart_container.columnconfigure(0, weight=1)
        self.cart_inner = self._make_scrollable(
            self.cart_container, bg=COLORS["panel"])

        totals = ttk.Frame(panel, style="Panel.TFrame", padding=(0, 12, 0, 4))
        totals.grid(row=3, column=0, sticky="ew")
        totals.columnconfigure(1, weight=1)

        ttk.Label(totals, text="Subtotal",
                  style="TotalsLine.TLabel").grid(row=0, column=0, sticky="w")
        self.subtotal_lbl = ttk.Label(totals, text=f"{CURRENCY}0.00",
                                      style="TotalsValue.TLabel")
        self.subtotal_lbl.grid(row=0, column=1, sticky="e")

        ttk.Label(totals, text="Tax (5%)",
                  style="TotalsLine.TLabel").grid(row=1, column=0,
                                                  sticky="w", pady=2)
        self.tax_lbl = ttk.Label(totals, text=f"{CURRENCY}0.00",
                                 style="TotalsValue.TLabel")
        self.tax_lbl.grid(row=1, column=1, sticky="e", pady=2)

        ttk.Separator(totals, orient="horizontal").grid(
            row=2, column=0, columnspan=2, sticky="ew", pady=(8, 6))

        ttk.Label(totals, text="Grand Total",
                  style="Grand.TLabel").grid(row=3, column=0, sticky="w")
        self.total_lbl = ttk.Label(totals, text=f"{CURRENCY}0.00",
                                   style="Grand.TLabel")
        self.total_lbl.grid(row=3, column=1, sticky="e")

        actions = ttk.Frame(panel, style="Panel.TFrame", padding=(0, 12, 0, 0))
        actions.grid(row=4, column=0, sticky="ew")
        actions.columnconfigure(0, weight=1)
        actions.columnconfigure(1, weight=2)

        ttk.Button(actions, text="Clear Cart", style="Ghost.TButton",
                   command=self._on_clear_cart
                   ).grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ttk.Button(actions, text="✓  Place Order", style="Big.TButton",
                   command=self._on_place_order
                   ).grid(row=0, column=1, sticky="ew")

    def _make_scrollable(self, parent, bg: Optional[str] = None) -> ttk.Frame:
        bg = bg or COLORS["panel"]
        canvas = tk.Canvas(parent, highlightthickness=0, bg=bg, bd=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical",
                                  command=canvas.yview)
        inner = ttk.Frame(canvas, style="Panel.TFrame")

        inner.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas_window = canvas.create_window((0, 0), window=inner, anchor="nw")

        def _resize(event):
            canvas.itemconfig(canvas_window, width=event.width)
        canvas.bind("<Configure>", _resize)

        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        return inner

    def _categories(self) -> List[str]:
        seen, out = set(), []
        for item in self.menu:
            if item.category not in seen:
                seen.add(item.category)
                out.append(item.category)
        return out

    def _filtered_items(self) -> List[MenuItem]:
        q = self.search_var.get().strip().lower()
        if not q or q == "search menu items…":
            return list(self.menu)
        return [m for m in self.menu
                if q in m.name.lower() or q in m.description.lower()]

    def _render_menu(self) -> None:
        items = self._filtered_items()
        items_by_cat: Dict[str, List[MenuItem]] = {c: [] for c in self._categories()}
        for it in items:
            items_by_cat[it.category].append(it)

        for category, frame in self.category_frames.items():
            for child in frame.winfo_children():
                child.destroy()

            frame.columnconfigure(0, weight=1)
            frame.columnconfigure(1, weight=1)

            cat_items = items_by_cat.get(category, [])
            if not cat_items:
                ttk.Label(
                    frame,
                    text="No items match your search in this category.",
                    style="Empty.TLabel", padding=20
                ).grid(row=0, column=0, columnspan=2, pady=24)
                continue

            for idx, item in enumerate(cat_items):
                r, c = divmod(idx, 2)
                card = MenuItemCard(frame, item, self.image_factory,
                                    on_add=self._on_add_to_cart)
                card.grid(row=r, column=c, sticky="nsew",
                          padx=10, pady=10, ipadx=2, ipady=2)

    def _render_cart(self) -> None:
        for child in self.cart_inner.winfo_children():
            child.destroy()

        if self.cart.is_empty:
            ttk.Label(self.cart_inner,
                      text="Your cart is empty.\nAdd something delicious!",
                      style="Empty.TLabel",
                      justify="center", padding=24
                      ).pack(expand=True, pady=40)
        else:
            for line in self.cart.lines.values():
                row = CartLineRow(self.cart_inner, line,
                                  on_inc=self._on_inc,
                                  on_dec=self._on_dec,
                                  on_remove=self._on_remove)
                row.pack(fill="x", pady=4, padx=4)

        self.subtotal_lbl.config(text=f"{CURRENCY}{self.cart.subtotal:.2f}")
        self.tax_lbl.config(text=f"{CURRENCY}{self.cart.tax:.2f}")
        self.total_lbl.config(text=f"{CURRENCY}{self.cart.grand_total:.2f}")

    def _on_add_to_cart(self, item: MenuItem) -> None:
        self.cart.add(item)
        self._render_cart()

    def _on_inc(self, item_id: str) -> None:
        self.cart.increase(item_id)
        self._render_cart()

    def _on_dec(self, item_id: str) -> None:
        self.cart.decrease(item_id)
        self._render_cart()

    def _on_remove(self, item_id: str) -> None:
        self.cart.remove(item_id)
        self._render_cart()

    def _on_clear_cart(self) -> None:
        if self.cart.is_empty:
            return
        if messagebox.askyesno("Clear cart",
                               "Remove all items from your cart?"):
            self.cart.clear()
            self._render_cart()

    def _on_place_order(self) -> None:
        if self.cart.is_empty:
            messagebox.showwarning(
                "Empty cart",
                "Your cart is empty. Add a few items before placing the order."
            )
            return

        try:
            result = self.order_writer.save(self.cart, customer_name="Guest")
        except OSError as exc:
            messagebox.showerror("Could not save order",
                                 f"Something went wrong while saving:\n{exc}")
            return

        self._show_receipt_dialog(result)
        self.cart.clear()
        self._render_cart()

    def _show_receipt_dialog(self, result: Dict) -> None:
        win = tk.Toplevel(self)
        win.title(f"Receipt — {result['order_id']}")
        win.configure(bg=COLORS["panel"])
        win.geometry("460x600")
        win.transient(self)

        ttk.Label(win, text="🎉  Order Placed Successfully!",
                  background=COLORS["panel"],
                  foreground=COLORS["ok"],
                  font=(FONT_FAMILY, 14, "bold"),
                  padding=(16, 14)).pack(anchor="w")

        ttk.Label(win,
                  text=f"Receipt saved to: {result['receipt_path']}",
                  background=COLORS["panel"],
                  foreground=COLORS["text_dim"],
                  font=(FONT_FAMILY, 9),
                  padding=(16, 0, 16, 8)).pack(anchor="w")

        txt_frame = ttk.Frame(win, style="Panel.TFrame", padding=12)
        txt_frame.pack(fill="both", expand=True)

        txt = tk.Text(txt_frame, wrap="none",
                      bg=COLORS["panel_alt"], fg=COLORS["text"],
                      font=("Courier New", 10),
                      relief="flat", borderwidth=0)
        txt.insert("1.0", result["receipt_text"])
        txt.config(state="disabled")
        txt.pack(fill="both", expand=True)

        ttk.Button(win, text="Close", style="Accent.TButton",
                   command=win.destroy).pack(pady=12, ipadx=20)

    def _install_placeholder(self, entry: ttk.Entry, text: str) -> None:
        entry.insert(0, text)
        entry.configure(foreground=COLORS["text_dim"])

        def on_focus_in(_):
            if entry.get() == text:
                entry.delete(0, "end")
                entry.configure(foreground=COLORS["text"])

        def on_focus_out(_):
            if not entry.get().strip():
                entry.insert(0, text)
                entry.configure(foreground=COLORS["text_dim"])

        entry.bind("<FocusIn>", on_focus_in)
        entry.bind("<FocusOut>", on_focus_out)

    def _build_logo_image(self) -> ImageTk.PhotoImage:
        size = 64
        img = Image.new("RGB", (size, size), COLORS["accent"])
        draw = ImageDraw.Draw(img)
        draw.ellipse((6, 6, size - 6, size - 6), fill=COLORS["bg"])
        font = PlaceholderImageFactory._load_font(int(size * 0.42))
        text = "C&C"
        bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text(((size - tw) / 2 - bbox[0], (size - th) / 2 - bbox[1]),
                  text, fill=COLORS["accent"], font=font)
        return ImageTk.PhotoImage(img)


# -----------------------------------------------------------------------------
# Entry point
# -----------------------------------------------------------------------------

def main() -> None:
    try:
        app = CoffeeMenuApp()
        app.mainloop()
    except Exception as exc:
        try:
            messagebox.showerror("Fatal error", str(exc))
        except Exception:
            print(f"[Fatal error] {exc}")
        raise


if __name__ == "__main__":
    main()