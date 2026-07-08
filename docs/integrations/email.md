# Email integration

BTU sends task notifications through Frappe's email stack.

## Configuration (15.2+)

1. Create or select a Frappe **Email Account** (SMTP).
2. Set **BTU Configuration → Default Email Account**.
3. Set **Environment Name** for subject/body prefix.

Migration from legacy BTU SMTP fields runs on `bench migrate`.

## Failure vs email failure

A failure to **send** email does not mark the underlying task as failed — task outcome and delivery are separate.

See [Email on failure recipe](../recipes/email-on-failure.md).
