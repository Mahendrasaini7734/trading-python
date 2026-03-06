# StackEarn Excel Upload Trading API

## Setup
1. Copy `.env.example` to `.env` and fill values.
2. Install requirements
3. Run FastAPI
4. Upload Excel file

### Run
```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Upload API
POST `/excel/upload-trade` (multipart/form-data file)

Excel sheet name: `signals`  
Required columns:
symbol, exchange, action, quantity, order_type, price, product_type, validity, tag  
Optional: remarks
