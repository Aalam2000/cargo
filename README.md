# CargoDB

**A platform for cargo companies: products, shipments, statuses, and finances.**

The core idea is to **work through an AI chat in Telegram**. You don't have to open a browser — many tasks are handled with a simple message to the bot. The web interface is there for full control, but Telegram is the fastest way to get started and handle day-to-day work.

---

## Get started in a minute — via Telegram

Bot: **[@cargo_adm_bot](https://t.me/cargo_adm_bot)**

Write to the bot in plain language — it will understand your request, perform the action, or tell you what to do next.

**Without signing up in the system, you can:**

- learn what the platform and bot can do;
- register a **new company** (name + administrator email);
- get step-by-step instructions.

**After linking Telegram to your account (Admin / Operator):**

- create a **client** by email;
- get help on any part of the system;
- handle work tasks without opening the CRM.

Example messages to the bot:

```
Help
How do I use the platform?
Create company "Bona Cargo", admin email: admin@example.com
Create client client@example.com
```

> The bot replies in the user's language. It understands messy and short messages — no need to memorize commands.

---

## Who it's for

| Who | How they work |
|-----|---------------|
| **Cargo company owner / administrator** | Sign up via the bot, configure reference data, oversee operations |
| **Operator** | Products, shipments, statuses, payments — in the browser or via the bot |
| **Cargo company client** | Personal account: their shipments, balance, contract, payments |

---

## What the platform does

### Products and shipments

- **Product** — a single client line item: description, weight, volume, warehouse, status, photos, QR code.
- **Shipment (cargo)** — several products from one client combined for transport.
- Changing a shipment's status or warehouse automatically updates all products inside it.
- Shipment contents can be **locked** to prevent accidental changes.
- PDF document per product for shipping paperwork.

### Statuses and tracking

- Configurable **shipment statuses** in company reference data.
- Home page tabs: **In transit**, **Delivered**, **Payments**.
- Filters by client and product number.

### Finance

- **Charges** and **payments** per client.
- Multiple currencies with exchange-rate conversion.
- **Client balance** and transaction history on the home page.
- QR code for payment in the client profile.

### Client portal

- View **their own** products and payments.
- Fill in profile and billing details (individual / legal entity).
- **Contract** — PDF generation, signing via email link.

### Reference data

Warehouses, cargo and packaging types, statuses, charge and payment types, **delivery tariffs**, exchange rates — all configurable for your company.

### Multilingual interface

Default language is Russian, with switching to English, Turkish, Chinese, Kazakh, Uzbek, Azerbaijani, Kyrgyz, and others.

---

## User roles

| Role | Access |
|------|--------|
| **Admin** | Full access: reference data, products, shipments, finance, Django Admin, AI chats |
| **Operator** | Same as Admin, without technical admin panel |
| **Client** | Own data only: products, payments, profile, contract |
| **WarehouseWorker** | Warehouse (QR scanning — in development), profile |

Each company's data is isolated — users only see their own organization.

---

## A typical workday

### Via Telegram (without logging into the CRM)

1. Message the bot — register a company or create a client.
2. Ask "how do I add a product?" or "how do I record a payment?" — the bot explains step by step.
3. Get answers to work questions in your language.

### In the web interface

1. Fill in **reference data** (warehouses, statuses, tariffs).
2. Create client **products**.
3. Build a **shipment** from products, update status when it moves.
4. Record a **charge** or **payment**, monitor balance on the home page.

### For clients

1. Log in with client code or email.
2. Sign the **contract**.
3. Track shipments and payments on the home page.

---

## CargoChat — AI automation

**CargoChat** is a separate product that connects to CargoDB.

It automates customer communication, document processing, and AI service workflows. Available to administrators from the web interface.

---

## In development

- Warehouse QR scanning (photo-based movement tracking).
- Dedicated **Payments** menu section (currently on the home page).
- Reports via the Telegram bot.
- Creating company users through the bot (partially enabled).

---

## Free to use

Community Edition is **free** for cargo companies of any size.

For more on the product strategy, see [VISION.md](VISION.md).
