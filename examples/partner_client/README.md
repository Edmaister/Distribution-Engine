# Partner Client Example

This example shows the intended external partner flow.

1. A system admin creates a partner client.
2. The partner exchanges `client_id` and `client_secret` for a bearer token.
3. The partner calls platform APIs with `Authorization: Bearer <token>`.

```bash
python examples/partner_client/python_client.py
```

Set these environment variables first:

- `AMPLIFI_API_BASE_URL`
- `AMPLIFI_CLIENT_ID`
- `AMPLIFI_CLIENT_SECRET`
- `AMPLIFI_SCOPE`

