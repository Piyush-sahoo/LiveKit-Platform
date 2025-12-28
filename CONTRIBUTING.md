# Contributing to Open Source Voice Agent Platform

First off, thank you for considering contributing to the Open Source Voice Agent Platform! It's people like you that make this platform such a great tool.

We welcome all types of contributions:
- 🐛 **Bug Fixes**: Solving issues to improve stability.
- 🌟 **New Features**: Adding capabilities to the platform.
- 📚 **Documentation**: Improving guides, API docs, and comments.
- ⚡ **Performance**: Optimizing latency and resource usage.

---

## 🚀 How to Contribute

### 1. Fork the Repository
Click the **Fork** button at the top right of the [GitHub repository page](https://github.com/Piyush-sahoo/Voice-AI-Platform) to create a copy of the repo in your own GitHub account.

### 2. Clone Your Fork
Clone your forked repository to your local machine:

```bash
git clone https://github.com/YOUR_USERNAME/Voice-AI-Platform.git
cd Voice-AI-Platform
```

### 3. Set Up Upstream Remote
Add the original repository as `upstream` to keep your fork synced:

```bash
git remote add upstream https://github.com/Piyush-sahoo/Voice-AI-Platform.git
git remote -v
```

### 4. Create a New Branch
**Always** create a new branch for your work. Do not commit directly to `main`.

```bash
# Sync with upstream first
git checkout main
git pull upstream main

# Create a feature branch
git checkout -b feature/amazing-new-feature
# OR for bug fixes
git checkout -b fix/issue-description
```

### 5. Make Your Changes
Write your code!
- **Backend**: Python (FastAPI). Follow PEP 8 standards. Use type hints.
- **Frontend**: React/Next.js. Use functional components and strict TypeScript.
- **Tests**: If you add code, add tests!

### 6. Verify Locally
Ensure everything works before committing.

```bash
# Run automation tests
python scripts/full_api_automation.py

# Run API key auth tests
python scripts/test_api_key_auth.py
```

### 7. Commit Your Changes
Use clear, conventional commit messages:

```bash
git add .
git commit -m "feat(backend): add support for Azure TTS"
#    ^ type     ^ scope      ^ description
```
*Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`.*

### 8. Push to Your Fork
```bash
git push origin feature/amazing-new-feature
```

### 9. Create a Pull Request (PR)
1. Go to your fork on GitHub.
2. Click **Compare & pull request**.
3. Fill out the PR template:
   - **Title**: Clear and descriptive.
   - **Description**: What does this PR do? Why is it needed?
   - **Screenshots**: (If UI changed).
   - **Testing**: How did you verify it?
4. Submit the PR!

---

## 🛠️ Development Guidelines

### Microservices Structure
- `backend/gateway`: API entry point. Don't put business logic here.
- `backend/services`: Core logic (Config, Analytics, etc.).
- `backend/shared`: Common code (DB models, Auth). **Reuse this!**

### Database Migrations
If you modify `shared/database/models.py`, ensure your changes are backward compatible or include a migration script.

### Environment Variables
Never commit `.env` files. If you add a new variable, update:
1. `.env.example`
2. `README.md` (if necessary)

---

## ❓ Getting Help
If you get stuck or have questions, please:
1. Check existing [GitHub Issues](https://github.com/Piyush-sahoo/Voice-AI-Platform/issues).
2. Start a [Discussion](https://github.com/Piyush-sahoo/Voice-AI-Platform/discussions).

Thank you for building with us! ❤️
