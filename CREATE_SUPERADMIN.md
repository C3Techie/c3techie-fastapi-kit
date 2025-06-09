## 🚀 How to Create a Superadmin User

Follow these steps to create a superadmin user in your `c3techie-fastapi-kit` project.

---

### 1. Register a New User

- Start your FastAPI server (see main setup instructions).
- Go to [http://localhost:8000/docs](http://localhost:8000/docs).
- Use the `/api/v1/users/` endpoint to register a new user.
- After registration, **copy the `id`** of your new user from the API response.

---

### 2. Enter the PostgreSQL Database (Docker)

Open a terminal and run:

```sh
docker compose exec db psql -U postgres -d <your-database-name>
```

> **Replace `<your-database-name>` with the database name you set in your `.env` or `docker-compose.yml` file.**

You should see the `=<your-database-name>=#` prompt.

---

### 3. (Optional) Verify the User and Get the Hashed Password

To check your user and see the hashed password (not required for superadmin creation, but useful for debugging):

```sql
SELECT id, username, email, password FROM users WHERE id = '<your-user-id>';
```

> **Replace `<your-user-id>` with the actual user ID you copied earlier.**

---

### 4. Insert a Superadmin Record

Run the following SQL to promote your user to superadmin:

```sql
INSERT INTO admins (
    id,
    user_id,
    role,
    permissions,
    assigned_at,
    is_active,
    created_at,
    updated_at
) VALUES (
    gen_random_uuid(),
    '<your-user-id>',
    'superadmin',
    ARRAY['manage_admins', 'system_settings'],
    NOW(),
    TRUE,
    NOW(),
    NOW()
);
```

---

### 5. (Optional) Set User as Superuser

To ensure your user has superuser privileges:

```sql
UPDATE users SET is_superuser = TRUE WHERE id = '<your-user-id>';
```

---

### 6. Confirm Superadmin Creation

You can verify your superadmin with:

```sql
SELECT * FROM admins WHERE role = 'superadmin' ORDER BY assigned_at DESC;
```

---

**You now have a superadmin user in your database!**

---

### 📝 Example

Suppose your user ID is `123e4567-e89b-12d3-a456-426614174000` and your database name is `myprojectdb`, your commands would look like:

```sh
docker compose exec db psql -U postgres -d myprojectdb
```

```sql
INSERT INTO admins (
    id,
    user_id,
    role,
    permissions,
    assigned_at,
    is_active,
    created_at,
    updated_at
) VALUES (
    gen_random_uuid(),
    '123e4567-e89b-12d3-a456-426614174000',
    'superadmin',
    ARRAY['manage_admins', 'system_settings'],
    NOW(),
    TRUE,
    NOW(),
    NOW()
);

UPDATE users SET is_superuser = TRUE WHERE id = '123e4567-e89b-12d3-a456-426614174000';
```

---

**Need help?**  
Open an issue or check the [docs](./docs) folder for more details.
