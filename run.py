from app import app
import os

if __name__ == '__main__':
    # For local development
    app.run(debug=True, host='0.0.0.0', port=5000)
else:
    # For production (Render)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)