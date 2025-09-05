from flask import Flask, render_template, request, redirect, url_for
from Main import TexasHoldem

app = Flask(__name__)

game = TexasHoldem()
game.start_hand()

@app.route('/')
def index():
    return render_template('index.html', game=game)

@app.route('/action', methods=['POST'])
def action():
    act = request.form.get('action')
    amount = int(request.form.get('amount', 0) or 0)
    game.process_action(act, amount)
    return redirect(url_for('index'))

@app.route('/new')
def new_hand():
    game.start_hand()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
