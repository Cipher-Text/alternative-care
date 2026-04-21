# 📚 AltCare Documentation

**Welcome to the AltCare documentation!** This is your central hub for all project documentation.

---

## 🎯 Quick Navigation by Role

### 👔 For Stakeholders & Product Managers
- [Project Overview](../README.md) - What is AltCare?
- [High-Level Roadmap](planning/roadmap.md) - 12-month plan (simplified)
- [Current Status](status/current.md) - Where we are now
- [Pricing & Plans](../README.md#pricing-plans) - Business model

### 💻 For Developers (Start Here!)
1. [Getting Started Guide](../GETTING_STARTED.md) - **Start here!**
2. [Complete Setup Guide](development/setup.md) - Detailed setup
3. [Backend Guide](development/backend.md) - Backend development
4. [Quick Reference](development/quick-reference.md) - Code snippets
5. [Testing Guide](development/testing.md) - Testing strategy
6. [i18n Guide](development/i18n.md) - Bilingual implementation

### 🏗️ For Architects & Tech Leads
- [Architecture Overview](architecture/overview.md) - System design
- [Database Schema](architecture/database.md) - All 30 tables
- [Tech Stack](architecture/tech-stack.md) - Technology decisions
- [Security & Auth](architecture/security.md) - Authentication, multi-tenancy

### 📋 For Project Planners
- [Roadmap (High-Level)](planning/roadmap.md) - Simplified view
- [Roadmap (Detailed)](planning/roadmap-detailed.md) - Full 12-month plan
- [Phase 1 Kickoff](planning/phase1-kickoff.md) - Phase 1 specifications
- [Phase 1 Tasks](planning/phase1-tasks.md) - Task breakdown
- [UX Improvements](planning/ux-improvements.md) - UX strategy

### 🤖 For AI Assistants
- [Current Status](status/current.md) - **SINGLE SOURCE OF TRUTH**
- [Architecture Overview](architecture/overview.md) - System structure
- [Development Setup](development/setup.md) - How to build
- [Project Structure](architecture/overview.md#project-structure) - Code organization

---

## 📖 Documentation Structure

```
docs/
├── README.md (you are here)        # Documentation map
│
├── architecture/                    # How the system is built
│   ├── overview.md                 # Architecture & design patterns
│   ├── database.md                 # Complete schema (30 tables)
│   ├── tech-stack.md              # Technology choices
│   └── security.md                 # Auth, multi-tenancy, security
│
├── development/                     # How to build the system
│   ├── setup.md                    # Complete setup guide
│   ├── backend.md                  # Backend development
│   ├── frontend.md                 # Frontend development (TBD)
│   ├── quick-reference.md         # Code snippets & patterns
│   ├── testing.md                  # Testing strategy
│   └── i18n.md                     # Bilingual (EN/BN) guide
│
├── planning/                        # What we're building & when
│   ├── roadmap.md                  # High-level roadmap
│   ├── roadmap-detailed.md        # Full 12-month plan
│   ├── phase1-kickoff.md          # Phase 1 specifications
│   ├── phase1-tasks.md            # Phase 1 task breakdown
│   └── ux-improvements.md         # UX strategy
│
├── api/                            # API documentation
│   └── (To be added as APIs are implemented)
│
└── status/                         # Where we are
    ├── current.md                  # Current status (SINGLE SOURCE)
    └── weekly-updates.md           # Progress log (TBD)
```

---

## 🚀 Common Workflows

### "I want to start developing"
1. Read [Getting Started](../GETTING_STARTED.md) (5 min)
2. Follow [Setup Guide](development/setup.md) (30 min)
3. Check [Current Status](status/current.md) (2 min)
4. Pick a task from [Phase 1 Tasks](planning/phase1-tasks.md)
5. Use [Quick Reference](development/quick-reference.md) while coding

### "I want to understand the architecture"
1. Read [Architecture Overview](architecture/overview.md) (10 min)
2. Browse [Database Schema](architecture/database.md) (reference)
3. Review [Tech Stack](architecture/tech-stack.md) (5 min)
4. Check [Security Design](architecture/security.md) (5 min)

### "I want to know the project status"
1. Read [Current Status](status/current.md) - **This is the single source of truth**

### "I want to plan my work"
1. Check [Current Status](status/current.md) - What's done
2. Read [High-Level Roadmap](planning/roadmap.md) - What's next
3. Review [Phase 1 Tasks](planning/phase1-tasks.md) - Specific tasks
4. Assign yourself a task

---

## 📝 Documentation Guidelines

### For Contributors

**When updating documentation:**

1. **Single Source of Truth** - Don't duplicate information
2. **Update Once** - If info exists in multiple places, consolidate it
3. **Link, Don't Repeat** - Reference other docs instead of copying
4. **Keep Current** - Update [status/current.md](status/current.md) weekly
5. **Use Metadata** - Add front matter to new docs:
   ```yaml
   ---
   title: Document Title
   audience: developers
   status: complete
   last_updated: 2026-04-21
   ---
   ```

**File Size Guidelines:**
- Status docs: ~200 lines (must be scannable)
- Guides: ~400 lines (tutorial-style)
- Reference: No limit (can be detailed)

**Cross-Reference Format:**
```markdown
See [Architecture Overview](architecture/overview.md) for system design.
```

---

## 🔍 Finding Information

### Search Priority

1. **This page** (docs/README.md) - Find the right document
2. **Current Status** (status/current.md) - For project status
3. **Getting Started** (../GETTING_STARTED.md) - For setup
4. **Quick Reference** (development/quick-reference.md) - For code examples
5. **GitHub search** - For code or specific terms

### Common Questions

**Q: Where do I start?**
→ [Getting Started Guide](../GETTING_STARTED.md)

**Q: What's the current project status?**
→ [Current Status](status/current.md)

**Q: How is the database structured?**
→ [Database Schema](architecture/database.md)

**Q: What technologies are we using?**
→ [Tech Stack](architecture/tech-stack.md)

**Q: How do I set up the backend?**
→ [Backend Guide](development/backend.md)

**Q: What's the roadmap?**
→ [High-Level Roadmap](planning/roadmap.md)

**Q: How do I write code for this project?**
→ [Quick Reference](development/quick-reference.md)

---

## 📞 Need Help?

- **Documentation issues**: Open an issue with the `documentation` label
- **Technical questions**: See [Backend Guide](development/backend.md) or [Quick Reference](development/quick-reference.md)
- **Project status**: Check [Current Status](status/current.md)
- **Everything else**: Start with [Getting Started](../GETTING_STARTED.md)

---

## 🎓 Learning Path

**New to the project? Follow this path:**

```
Day 1: Understanding
├─ Read: ../README.md (15 min)
├─ Read: status/current.md (5 min)
└─ Read: architecture/overview.md (15 min)

Day 2: Setup
├─ Follow: ../GETTING_STARTED.md (30 min)
├─ Follow: development/setup.md (1 hour)
└─ Verify: Backend running at localhost:8000

Day 3: Development
├─ Read: development/backend.md (20 min)
├─ Browse: development/quick-reference.md (10 min)
├─ Pick task: planning/phase1-tasks.md
└─ Start coding!

Ongoing:
└─ Reference: Use quick-reference.md and architecture docs
```

---

**Last Updated:** April 21, 2026  
**Maintained By:** Product & Engineering Team  
**Status:** Complete and active ✅

**Ready to start?** → [Getting Started Guide](../GETTING_STARTED.md)
