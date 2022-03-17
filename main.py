from flask import Flask, request, render_template, make_response
from GetCsv import make_df
import os

app = Flask(__name__)


@app.route('/', methods=["GET", "POST"])
def index():
    title = 'ウォレットアドレスを入力してください'

    if request.method == 'GET':
        return render_template('index.html', title=title)
    else:
        a = request.form.get('address')
        df = make_df(a)
        resp = make_response()
        resp.data = df.to_csv()
        resp.headers["Content-Disposition"] = "attachment; filename=%s" % a+'.csv'
        resp.headers["Content-Type"] = "text/csv"
        return resp


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get('PORT', 8080)))
