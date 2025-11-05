# PHASE1: Cost Agent - Comprehensive Documentation (Part 4/5)

**Document Part**: D.4 - Configuration, Testing, Deployment

---

## 10. Configuration
```bash
GROQ_API_KEY=your_key
PORT=8001
GROQ_MODEL=gpt-oss-20b
```

---

## 11. Testing
- Unit Tests: 80%+
- Integration Tests: 70%+

```bash
pytest tests/ -v --cov=src
```

---

## 12. Deployment
```bash
pip install -r requirements.txt
python -m uvicorn src.main:app --port 8001
```

---

**End of Part 4/5**
