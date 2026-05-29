# kualia.ai — Product Roadmap

## Completed

### Platform Foundation
- [x] Next.js frontend with Tailwind CSS dark theme
- [x] FastAPI backend with SQLAlchemy + SQLite
- [x] Docker Compose deployment (Hetzner VPS)
- [x] Nginx reverse proxy

### Authentication & Users
- [x] Clerk authentication (Google, GitHub, email)
- [x] User dashboard with sidebar navigation
- [x] Profile settings page
- [x] User-owned environments, training runs, research projects

### Environment Builder
- [x] AI-powered environment generation (natural language → Gymnasium code)
- [x] Multi-model support: Kimi K2.5 → Claude Sonnet → OpenAI fallback
- [x] Automated testing & self-correction loop (sandbox runner)
- [x] Environment versioning and rollback
- [x] Code tab with automatic annotation (obs/action/reward)
- [x] Docs tab with environment & training documentation
- [x] Builder ↔ Dashboard sidebar integration (breadcrumbs)
- [x] Environment naming (custom names)
- [x] GitHub export (env code + trained model to user's repo)

### Agent Training
- [x] SB3 training (PPO, DQN, SAC) with subprocess isolation
- [x] Real-time training curves (reward, loss, episode length)
- [x] Training history with expandable experiment details
- [x] Continue training from previous checkpoint
- [x] Training progress indicators in environment list

### Research Lab
- [x] Multi-agent research pipeline (Sage + Atlas)
- [x] 6-phase workflow: Research → Design → Experiment → Analyze → Write → Review
- [x] ArXiv paper search and import
- [x] Real environment generation during Design phase
- [x] Real agent training during Experiment phase
- [x] Paper generation with actual experimental data
- [x] PDF download for research papers
- [x] "Create Paper" from existing environment (builder integration)
- [x] Phase locking to prevent duplicate execution
- [x] Skip training on environments with <75% test pass rate
- [x] Environment deletion within Research Lab
- [x] "Search More" references button
- [x] Brief description as primary research focus in prompts

### Public Pages
- [x] Landing page with product showcase
- [x] Environment Generation feature page
- [x] Research Lab feature page
- [x] Comprehensive documentation page (sidebar + content)
- [x] Blog system with admin publishing
- [x] Template environment catalog

### Admin Panel
- [x] Environment generation (same quality as web builder)
- [x] Blog management with publish/unpublish
- [x] Admin-created content filtered from user dashboards

### UX Polish
- [x] Logged-in users: dashboard as homepage, hide public nav links
- [x] Sign-out button with Clerk profile styling
- [x] Empty state: inline builder prompt on dashboard
- [x] "+New Environment" modal for subsequent environments
- [x] Footer hidden for authenticated users
- [x] Delete options for environments and research projects
- [x] Pagination on list pages
- [x] Recent Research Projects on dashboard overview

### Rate Limiting
- [x] slowapi middleware on FastAPI
- [x] Per-endpoint limits for LLM-heavy routes (generate: 5/min, train: 10/min, chat: 20/min)
- [x] User-based (Clerk ID) and IP-based key functions

### Error Boundaries
- [x] Root error.tsx and global-error.tsx
- [x] Dashboard error boundary
- [x] Builder error boundary
- [x] Research Lab error boundary
- [x] 404 not-found.tsx

### Mobile Responsive
- [x] Navbar hamburger menu with mobile links
- [x] Landing page hero responsive typography (text-3xl → text-7xl)
- [x] Dashboard sidebar → mobile horizontal tabs
- [x] Builder two-column → mobile stack
- [x] Dashboard header flex-wrap (sm:flex-row)
- [x] Credit display in mobile navbar
- [x] Feedback link in mobile dashboard nav
- [x] Global padding adjustments (px-4 on mobile)

### Email System
- [x] Resend integration for transactional + marketing emails
- [x] 9 HTML email templates with kualia.ai branding
- [x] AI Email Marketing Agent (weekly tips, feature announcements, re-engagement)
- [x] Campaign management in admin panel with preview
- [x] Cloudflare Email Routing (support@kualia.ai, ali@kualia.ai)
- [x] Gmail Send-As with Resend SMTP

### Domain & SSL
- [x] kualia.ai domain (GoDaddy → Cloudflare)
- [x] SSL via Let's Encrypt
- [x] Cloudflare DNS management

### Subscription & Credits
- [x] Token-based credit system (10x markup on LLM costs)
- [x] Pricing plans: Free ($5 welcome) / Starter ($19) / Pro ($49) / Lab ($149)
- [x] Plan limits enforcement (env count, training)
- [x] Pricing page

### Marketing & GTM
- [x] GTM Engineer Agent (automated Twitter marketing for kualia.ai)
- [x] Visual content generation for tweets
- [x] Science Bot (RL/AI tweets — English + Turkish)
- [x] Admin marketing module with analytics

### Admin CRM
- [x] Users module (registered users list)
- [x] Environments module (generated envs list)
- [x] Papers module (research papers list)
- [x] Agents module (AI agent profiles, skills, config)

---

## In Progress — Pre-Launch

### Stripe Integration
- [ ] Stripe checkout for plan upgrades
- [ ] Webhook handling (subscription created/cancelled/updated)
- [ ] Subscription management page in user settings
- [ ] Credit top-up purchasing

### Legal
- [ ] Terms of Service page at /terms
- [ ] Privacy Policy page at /privacy
- [ ] Footer links

### Clerk Production
- [ ] Switch from dev to production keys
- [ ] Configure production OAuth redirects

---

## Planned — Phase 2 (Post-Launch)

### Infrastructure
- [ ] PostgreSQL migration (replace SQLite)
- [ ] Automated backups (DB + trained models)
- [ ] Sentry error tracking
- [ ] CI/CD pipeline (GitHub Actions)

### GPU Training
- [ ] Integration with cloud GPU providers (RunPod / Modal / Lambda)
- [ ] Support for 1M+ timestep training runs
- [ ] Training queue management

### Experiment Tracking
- [ ] Multi-algorithm comparison on same environment
- [ ] Side-by-side training curve comparison
- [ ] WandB / MLflow integration option

### Collaboration
- [ ] Shared workspaces for teams
- [ ] Environment forking from community catalog
- [ ] Real-time collaboration on research projects

### Advanced Features
- [ ] Multi-agent environment support
- [ ] Model export (ONNX, TorchScript)
- [ ] Environment composition (combine simple envs)
- [ ] Real-time training via WebSocket
- [ ] Onboarding flow / guided tour
