from bson import ObjectId
from bson.json_util import dumps
from flask import Response
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_restful import Resource
from mongoengine.errors import DoesNotExist

from database.model import Item, Board
from resources.errors import InternalServerError, ItemNotExistsError
import json


class ByBoardApi(Resource):
    """[Batch Comment actions]
    """

    @jwt_required()
    def get(self, id):
        """[Retrieves all Items under a board]

        Raises:
            InternalServerError: [If Error in retrieval]

        Returns:
            [json] -- [Json object with message and status code]
        """
        try:
            print(id)
            user_id = get_jwt_identity()
            user_board = Board.objects.get(slug=id, added_by=user_id)
            # posts = Item.objects.aggregate(
            #     {"$lookup": {
            #         "from": "board",
            #         "foreignField": "_id",
            #         "localField": "board",
            #         "as": "board",
            #     }},
            #     {"$unwind": "$Board"},
            #     {"$match": {"board._id": ObjectId(id)}},
            #     {
            #         "$addFields": {
            #             "liked": {
            #                 "$in": [user_id, "$liked_by"]
            #             }
            #         }
            #     }, {"$sort": {"created_at": 1}})
            items = Item.objects(board=user_board.id, added_by=user_id).to_json()
            data = json.dumps(
                {'data': json.loads(items), 'message': "Successfully retrieved", "count": len(json.loads(items))})
            return Response(data, mimetype="application/json", status=200)
        except  DoesNotExist:
            raise ItemNotExistsError
        except Exception as e:
            print(e)
            raise InternalServerError
