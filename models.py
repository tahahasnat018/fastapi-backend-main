from sqlalchemy import (
    Column, Integer, String, DateTime, Float, Boolean,
    ForeignKey
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

# ----------------------------
# Vendor Table
# ----------------------------
class Vendor(Base):
    __tablename__ = "vendorcase1"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    contact_person = Column(String)
    email = Column(String)
    password = Column(String)
    email_verified = Column(Boolean)
    phone = Column(String)
    logo = Column(String)
    active = Column(Boolean)
    created_at = Column(DateTime)  # Removed default
    updated_at = Column(DateTime)  # Removed default/onupdate
    password_setup_token = Column(String)
    reactivation_date = Column(DateTime)
    role_type = Column(Integer)
    lat = Column(Float)
    lon = Column(Float)
    payment_mode_type_id = Column(Integer)
    business_cert_url = Column(String)
    license_cert_url = Column(String)
    delivery_time = Column(Integer)
    delivery_time_type_id = Column(Integer)
    delivery_charges_type_id = Column(Integer)
    delivery_charges = Column(Float)
    covering_radius = Column(Float)
    business_cert_url_change_status_id = Column(Integer)
    license_cert_url_change_status_id = Column(Integer)
    delivery_time_change_status_id = Column(Integer)
    covering_radius_change_status_id = Column(Integer)
    transport_type_id = Column(Integer)
    cash = Column(Boolean)
    card = Column(Boolean)
    bank_transfer = Column(Boolean)
    token = Column(String)
    business_name = Column(String)
    shop_address = Column(String)
    city = Column(String)
    province_id = Column(Integer)
    postal_code = Column(Integer)
    country_id = Column(Integer)

    orders = relationship("OrderCase1", back_populates="vendor")

    # Renamed to avoid conflict — maps to InventoryCase1 table
    inventories_case1 = relationship("InventoryCase1", back_populates="vendor")

    # Maps to Inventory table
    inventories = relationship("Inventory", back_populates="vendor")


# ----------------------------
# InventoryCase1 Table
# ----------------------------
class InventoryCase1(Base):
    __tablename__ = "inventorycase1"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    photo_url = Column(String)
    ingredient_type_id = Column(Integer)
    price_per_unit = Column(String)
    barcode = Column(String)
    unit_quantity = Column(Integer)
    unit_type_id = Column(Integer)
    created_at = Column(DateTime)  # Removed default
    updated_at = Column(DateTime)  # Removed default/onupdate
    available = Column(Boolean, default=True)
    vendor_id = Column(Integer, ForeignKey("vendorcase1.id"))
    barcode_url = Column(String)
    min_order_quantity = Column(Integer)

    vendor = relationship("Vendor", back_populates="inventories_case1")
    mappings = relationship("OrderCase1InventoryMapping", back_populates="inventory")
    wastages = relationship("Wastage", back_populates="inventory")


# ----------------------------
# Inventory Table
# ----------------------------
class Inventory(Base):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    photo_url = Column(String)
    ingredient_type_id = Column(Integer)
    price_per_unit = Column(String)  # E.g. "500 PKR"
    barcode = Column(String)
    unit_quantity = Column(Integer)
    unit_type_id = Column(Integer)
    created_at = Column(DateTime)  # Removed default
    updated_at = Column(DateTime)  # Removed default/onupdate
    is_assigned = Column(Boolean, default=False)
    available = Column(Boolean, default=True)
    min_threshold = Column(Integer)
    max_threshold = Column(Integer)
    vendor_id = Column(Integer, ForeignKey("vendorcase1.id"))
    current_stock = Column(Integer)
    user_id = Column(Integer)

    vendor = relationship("Vendor", back_populates="inventories")
    menu_uses = relationship("MenuIngredient", back_populates="ingredient")


# ----------------------------
# OrderCase1 Table
# ----------------------------
class OrderCase1(Base):
    __tablename__ = "ordercase1"

    id = Column(Integer, primary_key=True, index=True)
    delivery_date = Column(DateTime)
    status_type_id = Column(Integer)
    created_at = Column(DateTime)  # Removed default
    updated_at = Column(DateTime)  # Removed default/onupdate
    business_owner_id = Column(Integer)
    comment = Column(String)
    vendor_id = Column(Integer, ForeignKey("vendorcase1.id"))

    vendor = relationship("Vendor", back_populates="orders")
    mappings = relationship("OrderCase1InventoryMapping", back_populates="order")


# ----------------------------
# OrderCase1InventoryMapping Table
# ----------------------------
class OrderCase1InventoryMapping(Base):
    __tablename__ = "ordercase1_inventory_mapping"

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("ordercase1.id"))
    inventory_id = Column(Integer, ForeignKey("inventorycase1.id"))
    quantity = Column(Integer)
    created_at = Column(DateTime)  # Removed default
    updated_at = Column(DateTime)  # Removed default/onupdate

    order = relationship("OrderCase1", back_populates="mappings")
    inventory = relationship("InventoryCase1", back_populates="mappings")


# ----------------------------
# SMEmployeeRoleType Table
# ----------------------------
class SMEmployeeRoleType(Base):
    __tablename__ = "sm_employeeroletype"

    id = Column(Integer, primary_key=True, index=True)
    business_owner_id = Column(Integer)
    value = Column(String, nullable=False)
    code = Column(String, nullable=True)
    created_at = Column(DateTime)  # Removed default
    updated_at = Column(DateTime)  # Removed default/onupdate


# ----------------------------
# StatusType Table
# ----------------------------
class StatusType(Base):
    __tablename__ = "statuscase1_type"

    id = Column(Integer, primary_key=True)
    code = Column(String)
    value = Column(String)
    created_at = Column(DateTime)  # Removed default
    updated_at = Column(DateTime)  # Removed default/onupdate


# ----------------------------
# Wastage Table
# ----------------------------
class Wastage(Base):
    __tablename__ = "wastage"

    id = Column(Integer, primary_key=True)
    business_owner_id = Column(Integer)
    ingredient_id = Column(Integer, ForeignKey("inventorycase1.id"))
    unit_type = Column(String)
    wastage_qty = Column(Float)
    loss_value = Column(Float)
    created_at = Column(DateTime)  # Removed default
    updated_at = Column(DateTime)  # Removed default/onupdate

    inventory = relationship("InventoryCase1", back_populates="wastages")


# ----------------------------
# Menu Table
# ----------------------------
class Menu(Base):
    __tablename__ = "menu"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    name = Column(String)
    description = Column(String)
    photo = Column(String)
    price = Column(Float)
    currency = Column(String)
    quantity = Column(Integer)
    weight = Column(Float)
    menu_category_id = Column(Integer)
    datetime = Column(DateTime)
    created_at = Column(DateTime)  # Removed default
    updated_at = Column(DateTime)  # Removed default/onupdate

    ingredients = relationship("MenuIngredient", back_populates="menu")
    customer_order_mappings = relationship("CustomerOrderMenuMapping", back_populates="menu")


# ----------------------------
# CustomerOrder Table
# ----------------------------
class CustomerOrder(Base):
    __tablename__ = "customer_order"

    id = Column(Integer, primary_key=True)
    delivery_datetime = Column(DateTime)
    status_type_id = Column(Integer)
    customer_id = Column(Integer)
    employee_id = Column(Integer)
    created_at = Column(DateTime)  # Removed default
    updated_at = Column(DateTime)  # Removed default/onupdate
    user_id = Column(Integer)
    menu_category_id = Column(Integer)
    order_type_id = Column(Integer)
    price = Column(Float)

    menu_mappings = relationship("CustomerOrderMenuMapping", back_populates="customer_order")


# ----------------------------
# CustomerOrderMenuMapping Table
# ----------------------------
class CustomerOrderMenuMapping(Base):
    __tablename__ = "customer_order_menu_mapping"

    id = Column(Integer, primary_key=True)
    menu_id = Column(Integer, ForeignKey("menu.id"))
    customer_order_id = Column(Integer, ForeignKey("customer_order.id"))
    created_at = Column(DateTime)  # Removed default
    updated_at = Column(DateTime)  # Removed default/onupdate

    menu = relationship("Menu", back_populates="customer_order_mappings")
    customer_order = relationship("CustomerOrder", back_populates="menu_mappings")


# ----------------------------
# MenuIngredient Table
# ----------------------------
class MenuIngredient(Base):
    __tablename__ = "menu_ingredient"

    id = Column(Integer, primary_key=True)
    menu_id = Column(Integer, ForeignKey("menu.id"))
    ingredient_id = Column(Integer, ForeignKey("inventory.id"))
    quantity = Column(String)  # Quantity with units like '5kg'
    unit_type_id = Column(Integer)

    menu = relationship("Menu", back_populates="ingredients")
    ingredient = relationship("Inventory", back_populates="menu_uses")
