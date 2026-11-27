# ErisPulse Workbench

> [!TIP]
> **When to read this**: When you want to submit a module/adapter to the module store, apply for a `plugin-xxx.erisdev.com` website address, automatically submit modules via script or CI, or enable your own website to support "login with ErisPulse account", read this. Skip if not needed.

[ErisPulse Workbench](https://workbench.erisdev.com/) is the **unified account center and creator backend** of the ecosystem: one account connects the module store, hosted domains, and open APIs. It is a fully online service that **requires no package installation**—just open the webpage, log in, and you're ready to use it.

```text
GitHub / Codeberg / Yunhu / Email login
            │
            ▼
      ErisPulse Account ──── Two-factor authentication (optional)
            │
   ┌────────┼─────────────┬──────────────┐
   ▼        ▼             ▼              ▼
Module Management   Hosted Domains   Access Tokens   OAuth Applications
(Store)           (Website Addresses) (Scripts/CI) (Third-party Login)
```

---

## Login and Account

The Workbench supports four login methods. Unconfigured login methods will not appear on the login page:

| Method | Applicable Scenario |
|--------|---------------------|
| GitHub | Authors whose module code is hosted on GitHub |
| Codeberg | Authors whose module code is hosted on Codeberg |
| Yunhu | Users using the Yunhu platform |
| Email | Users without the above accounts: username + email + password; during registration, a 6-digit verification code received by email is required |

> [!NOTE]
> The same account can bind multiple login identities on the "Profile" page. After logging in with different methods and binding them together, you can access the same account using any of the methods next time.

**Two-factor authentication**: On the "Profile" page, you can enable two-factor authentication based on Time-based One-Time Password (TOTP). Just scan the QR code with any authenticator app. After enabling, dynamic codes are required for login and sensitive operations such as deleting modules or domains.

> [!WARNING]
> The TOTP secret key is **only displayed once when enabled**. If you lose the key, you won't be able to log in. Please save it securely.

---

## Module Management

All modules and adapters in the module store are managed in the Workbench.

### Submitting a Module

1. Go to "Submit New Module" on the left.
2. Fill in the form:

| Field | Description |
|-------|-------------|
| Name | Module name, consistent with the entry-point key |
| Type | `module` (functional module) or `adapter` (adapter) |
| PyPI Package Name | e.g., `ErisPulse-MyModule` |
| Description | At least 10 characters |
| Author | Author name displayed in the store |
| Repository URL | Repository on `github.com` or `codeberg.org` |
| Category | Tools / Entertainment / Management / Notifications / AI / Platform / Analysis |
| Tags, Multi-language, Minimum SDK Version | Optional |

3. After submission, the module is distributed via the module index repository and usually appears in the store within a few minutes.

Newly submitted modules are initially marked as "Unverified"—indicating they have not yet passed official review. Users will receive a risk warning when installing. After review, the status changes to "Verified".

### Editing and Batch Operations

In the "Module List," go to your module's detail page to modify all metadata such as description, repository URL, category, tags, upload module icons; you can also enable multi-select mode to **batch verify / unverify / delete** multiple modules (only one dynamic code input is required for batch operations).

### Claiming Ownership

Modules already in the store but not submitted by you (e.g., previously collected by someone else) can be claimed back to your account:

- **Automatic Claiming**: Log in with the same GitHub/Codeberg account as the module repository. When the system identifies matching repository ownership, the claim is automatically completed.
- **Manual Claiming**: On the module detail page, click "Claim This Module" and fill in the reason. The transfer is processed after administrator review.

---

## Hosted Domains

Each module that has been indexed can apply for a free website address in the format `plugin-ModuleName.erisdev.com`, used for hosting the module's homepage, documentation, or demo site.

| Limit | Value |
|-------|-------|
| Per module | 2 domains |
| Per account | 10 domains |
| Unverified | Released after 7 days, allowing others to reapply the domain |

### Four Ways to Connect

| Method | How to Use | Suitable For |
|--------|------------|--------------|
| **Repository Branch** (Recommended) | Fill in the repository URL and branch name; the Workbench directly reads static files from this branch | The site source code is in the module repository; updates are pushed automatically |
| **Redirect** | 301 redirect to your specified `https://` address when accessing this domain | Already have your own website and just want a memorable entry point |
| **Your Own Server** | Add a CNAME/A/AAAA record pointing to your server | You have deployed the site yourself |
| Upload Static Site | Upload a zip package, hosted by platform object storage | Currently limited to internal testing, not fully open |

For the "Repository Branch" method, the branch name is defaulted to `ep-site`—a conventionally used branch name for the site. It is recommended to place the site files in this separate branch to avoid contaminating the main branch code.

### Application Process

1. Go to "Hosted Domains" on the left and select the module to which you want to attach the domain (only modules under your name are selectable).
2. Fill in the prefix; availability is checked in real time as you type. The prefix only allows lowercase letters, numbers, and hyphens in the middle.
3. Select the connection method and fill in the corresponding information, then submit.

**Review Rules**: The **first domain** for each module is activated directly; from the second onwards, administrator review is required. The review result will be notified via email.

### Ownership Verification

To prevent someone from pointing a domain to a repository or server that does not belong to them, "Repository Branch" and "Your Own Server" methods require ownership verification:

| Method | Verification Method |
|--------|---------------------|
| Repository Branch | Place a file `erisdev-site-verify.txt` in the root directory of the branch, with the verification code provided by the Workbench as content |
| Your Own Server | Provide `/.well-known/erisdev-verify.txt` on your server, with the same content as above |

After placing the file, return to the Workbench and click "Complete Verification." Before verification, accessing the domain will display a "Waiting for Ownership Verification" notice page.

### Management Operations

On each domain card, you can:

- **Pause / Resume**: After pausing, accessing displays "Site Paused," but the content is retained.
- **Delete**: Releases the domain and all associated resources, requiring a dynamic code input.
- **Change Repository or Branch**: After modification, the domain returns to the pending verification state; re-verification is required for the changes to take effect.

---

## Open APIs

The Workbench is also an OAuth 2.0 authorization server, providing two types of capabilities externally.

### Access Tokens

When scripts or CI use the Workbench API (e.g., for automatic module submission), use access tokens instead of account passwords:

1. Go to "Open Platform → Access Tokens," fill in the name, and click "Generate Token."
2. The token format is `epat_` + 40 hexadecimal digits, **displayed only once upon generation.**
3. Include the token in the `Authorization: Bearer epat_…` header for requests.

Each account can have up to 10 tokens. If two-factor authentication is enabled, you can check "No Dynamic Code Required"—afterward, using this token to call sensitive interfaces will no longer require a dynamic code, suitable for unattended CI.

> [!TIP]
> The request body must be UTF-8 encoded JSON. Windows terminals default to GBK, and directly passing Chinese characters will be rejected by the server—first execute `chcp 65001`, or save the request body as a file and submit it using `curl --data-binary @body.json`.

### OAuth Applications

To enable your own website or tool to support "login with ErisPulse account":

1. Go to "Open Platform" and register an application: fill in the name and callback address (multiple are allowed).
2. Obtain `client_id` and `client_secret`—**the secret is displayed only once**, and can be reset at any time.
3. Integrate according to the standard OAuth 2.0 authorization code flow:

| Endpoint | Purpose |
|----------|---------|
| `/oauth/authorize` | Redirect users to authorize |
| `/oauth/token` | Exchange authorization code for token |
| `/api/userinfo` | Get user information (excluding email) using the token |

Each account can register up to 5 applications.

---

## Other Pages

- **Ecosystem Updates**: Summarizes version releases and issues in the ErisPulse main repository and module index repository.
- **Usage Documentation**: Built-in usage instructions in the Workbench, corresponding to the content of this document, supporting five languages.

---

## Frequently Asked Questions

### Why doesn't my submitted module appear in the store immediately?

Module indexing is asynchronously distributed via the module index repository and usually takes a few minutes to take effect. You can check the operation status in the module list; "Applied" indicates success.

### Why does domain verification keep failing?

Ensure the **path and content** of the verification file exactly match what is displayed in the Workbench (paths are case-sensitive, and content should have no extra spaces or line breaks). For the "Repository Branch" method, also confirm the file is in the branch you specified.

### How long does it take for a domain to become active after application?

For "Repository Branch" and "Redirect" methods, activation is immediate after verification. For "Your Own Server" method, it also requires waiting for DNS records to propagate globally, usually a few minutes.

---

## Next Steps

- **Ready to publish your module to PyPI**: [Publishing and Module Store Guide](../developer-guide/publishing.md) (includes a complete example for submitting via API)
- **Don't have a module to publish yet**: [Getting Started with Module Development](../developer-guide/modules/getting-started.md)
- **Want to see what modules are available in the store**: [Ecosystem Overview](README.md)