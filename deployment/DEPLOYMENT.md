# Atlanta Sentinel - Multi-Application Subdomain Deployment & HTTPS Guide

This system deploys three completely separate, independent applications connected to one shared backend and SQLite database:

| Application | Deployment URL | Purpose | Access Interface |
| :--- | :--- | :--- | :--- |
| **Tourist Application** | `https://tourist.yourdomain.com` | Standalone installable mobile PWA for visitors | Opens directly to Tourist Login / Register |
| **Admin Web Application** | `https://admin.yourdomain.com` | Desktop command center for administrators | Opens directly to Admin Command Login |
| **Police Patrol Application** | `https://police.yourdomain.com` | Mobile CAD terminal for active patrol officers | Opens directly to Police Patrol Login |

---

## 1. Domain & DNS Configuration

At your domain registrar (e.g., Cloudflare, Namecheap, Route53), add the following DNS records pointing to your server's public IP address:

```dns
Type    Name       Content          TTL     Proxy Status
A       tourist    203.0.113.10     Auto    DNS Only (or Proxied)
A       admin      203.0.113.10     Auto    DNS Only (or Proxied)
A       police     203.0.113.10     Auto    DNS Only (or Proxied)
```

---

## 2. HTTPS & SSL Certificate Setup (Let's Encrypt / Certbot)

Run Certbot to obtain free SSL/TLS certificates for all three subdomains:

```bash
sudo certbot certonly --nginx -d tourist.yourdomain.com -d admin.yourdomain.com -d police.yourdomain.com
```

Or using DNS challenge for wildcards:
```bash
sudo certbot certonly --manual --preferred-challenges dns -d *.yourdomain.com -d yourdomain.com
```

---

## 3. Reverse Proxy Configuration

### Option A: Using Nginx
1. Copy `deployment/nginx.conf` to `/etc/nginx/sites-available/sentinel.conf`.
2. Replace `yourdomain.com` with your actual registered domain.
3. Enable the site and restart Nginx:
   ```bash
   sudo ln -s /etc/nginx/sites-available/sentinel.conf /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl reload nginx
   ```

### Option B: Using Caddy (Automated Zero-Config HTTPS)
Caddy automatically provisions and renews SSL certificates:
```bash
caddy run --config deployment/Caddyfile
```

---

## 4. Local Development & Subdomain Testing

To test the three actual subdomain URLs locally on your development machine, add these lines to your system's `hosts` file:

- **Windows**: `C:\Windows\System32\drivers\etc\hosts`
- **Linux/Mac**: `/etc/hosts`

```text
127.0.0.1 tourist.localhost
127.0.0.1 admin.localhost
127.0.0.1 police.localhost
```

You can now open in your browser:
- `http://tourist.localhost:5000` (Tourist Mobile App)
- `http://admin.localhost:5000` (Admin Command Web App)
- `http://police.localhost:5000` (Police Patrol CAD Terminal)

Path-based access is also available on any port without editing hosts:
- `http://localhost:5000/tourist`
- `http://localhost:5000/admin`
- `http://localhost:5000/police`

---

## 5. Default Provisioned Operational Credentials

| Portal | Default Email | Password | Role |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin@yourdomain.com` | `Admin@Sentinel2026!` | `admin` |
| **Police** | `police@yourdomain.com` | `Police@Sentinel2026!` | `police` (Badge: APD-504) |
| **Tourist** | *(Self-register on login screen)* | *(User-chosen)* | `tourist` |

*Credentials can be configured via environment variables: `ADMIN_EMAIL`, `ADMIN_PASSWORD`, `POLICE_EMAIL`, `POLICE_PASSWORD`.*
