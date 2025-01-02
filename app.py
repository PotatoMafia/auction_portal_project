from datetime import datetime

from flask import Flask, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from models import Bid, Auction
from services import UserService, AuctionService
from extensions import db

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///auction_portal.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'AAAAAAAAAAAAAAA'

db.init_app(app)

# Routes
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    return jsonify(UserService.register_user(data)), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    response, status_code = UserService.login_user(data)
    return jsonify(response), status_code

@app.route('/auctions', methods=['GET'])
def get_auctions():
    return jsonify(AuctionService.get_all_auctions()), 200

@app.route('/auctions/<int:auction_id>', methods=['GET'])
def get_auction(auction_id):
    return jsonify(AuctionService.get_auction_details(auction_id)), 200

@app.route('/bid', methods=['POST'])
@jwt_required()
def place_bid():
    data = request.json
    user_id = get_jwt_identity()
    auction = Auction.query.get_or_404(data['auction_id'])
    if auction.end_time < datetime.utcnow():
        return jsonify({'message': 'Auction has ended'}), 400
    bid = Bid(auction_id=data['auction_id'], user_id=user_id, bid_price=data['bid_price'])
    db.session.add(bid)
    db.session.commit()
    return jsonify({'message': 'Bid placed successfully'}), 201

@app.route('/close_auction/<int:auction_id>', methods=['POST'])
@jwt_required()
def close_auction(auction_id):
    return jsonify(AuctionService.close_auction(auction_id)), 200

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
