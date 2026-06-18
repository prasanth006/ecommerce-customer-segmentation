import os
import numpy as np
import joblib
from flask import Flask, render_template, request

# Always resolve paths from the project root, no matter where the app is launched from
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(BASE_DIR, 'models')

# Load the trained model once, at startup
scaler = joblib.load(os.path.join(MODELS_DIR, 'scaler.pkl'))
kmeans = joblib.load(os.path.join(MODELS_DIR, 'kmeans.pkl'))
segment_map = joblib.load(os.path.join(MODELS_DIR, 'segment_map.pkl'))

# Short description + recommendation per segment (from our analysis)
SEGMENT_INFO = {
    'Champions':     ('Recent, frequent, high-spending — your best customers.',
                      'Reward and retain: VIP perks, early access, loyalty rewards.'),
    'Loyal':         ('Reliable repeat buyers with solid spend.',
                      'Nurture and upsell them toward Champion status.'),
    'New Customers': ('Bought recently but only once or twice — still warming up.',
                      'Strong onboarding and a second-purchase incentive.'),
    'Lost':          ('Have not purchased in a long time and rarely did.',
                      'A low-cost win-back campaign — keep spend efficient.'),
}

app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    if request.method == 'POST':
        try:
            recency = float(request.form['recency'])
            frequency = float(request.form['frequency'])
            monetary = float(request.form['monetary'])

            # Same pipeline as training: log1p -> scale -> predict
            x = np.log1p([[recency, frequency, monetary]])
            x_scaled = scaler.transform(x)
            cluster = int(kmeans.predict(x_scaled)[0])
            segment = segment_map.get(cluster, f'Cluster {cluster}')
            desc, rec = SEGMENT_INFO.get(segment, ('', ''))

            result = {'segment': segment, 'description': desc, 'recommendation': rec,
                      'recency': recency, 'frequency': frequency, 'monetary': monetary}
        except (ValueError, KeyError):
            result = {'error': 'Please enter valid numbers in all three fields.'}

    return render_template('index.html', result=result)


if __name__ == '__main__':
    app.run(debug=True)