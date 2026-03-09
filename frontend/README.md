# Frontend Banking App

## Folder Structure

- `index.html` - Public landing page
- `login.html` - Login page
- `register.html` - Registration + KYC onboarding page
- `customer.html` - Customer dashboard
- `admin.html` - Admin dashboard
- `assets/css/main.css` - Shared UI styles
- `assets/js/core/` - Shared app modules (`api`, `auth`, `storage`, `ui`, `config`)
- `assets/js/pages/` - Page-specific logic

## API Integration Examples

### Login (OAuth2 form)

```js
import { apiRequest } from "/assets/js/core/api.js";

const token = await apiRequest("/auth/token", {
  method: "POST",
  form: true,
  auth: false,
  body: { username: "user@example.com", password: "Secret123" },
});
```

### Create Customer Profile

```js
import { apiRequest } from "/assets/js/core/api.js";

const customer = await apiRequest("/customers", {
  method: "POST",
  body: {
    user_id: 12,
    kyc_full_name: "Jane Doe",
    kyc_document_id: "DOC-123",
  },
});
```

### Initiate Transfer

```js
import { apiRequest } from "/assets/js/core/api.js";

const transfer = await apiRequest("/transfers/initiate", {
  method: "POST",
  body: {
    from_account: 10,
    to_account: 11,
    amount: 75.5,
  },
});
```
