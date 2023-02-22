import json

from flask import Response, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_restful import Resource
from mongoengine.errors import FieldDoesNotExist, NotUniqueError, DoesNotExist, ValidationError, InvalidQueryError

from database.model import Board, User
from util.errors import SchemaValidationError, UpdatingItemError, ItemAlreadyExistsError, InternalServerError, \
    DeletingItemError, ItemNotExistsError
import timeago, datetime
from bson.objectid import ObjectId
from bson.json_util import dumps


class BoardsApi(Resource):
    """[Batch Board actions]
    """

    @jwt_required()
    def get(self):
        """[Retrieves all Boards by user]

        Raises:
            InternalServerError: [If Error in retrieval]

        Returns:
            [json] -- [Json object with message and status code]
        """
        try:
            user_id = get_jwt_identity()
            user = User.objects(id=ObjectId(user_id)).only('username')
            now = datetime.datetime.now()
            boards = Board.objects(added_by=ObjectId(user_id))
            boards_list = []
            for board in boards:
                board_dict = board.to_mongo().to_dict()
                data = timeago.format(board.created_at, now)
                board_dict['time_stamp'] = data
                board_dict['username'] = user[0].username
                boards_list.append(board_dict)
            res = {'data': boards_list, 'message': "Successfully retrieved", "count": len(boards_list)}
            boards_josn = dumps(res)
            return Response(boards_josn, mimetype="application/json", status=200)


        except Exception as e:
            print(e)
            raise InternalServerError

    @jwt_required()
    def post(self):
        """[Board API]

        Raises:
            SchemaValidationError: [If there are validation error in the board data]
            ItemAlreadyExistsError: [If the board already exist]
            InternalServerError: [Error in insertion]

        Returns:
            [json] -- [Json object with message and status code]
        # """

        body = request.get_json()
        # validations
        if 'title' not in body:
            raise SchemaValidationError

        try:
            user_id = get_jwt_identity()
            user = User.objects.get(id=user_id)
            board = Board(**body, added_by=user)
            board.save()
            slug = board.slug
            data = json.dumps(
                {'id': str(slug), 'message': "Successfully inserted", 'board': json.loads(board.to_json())})
            return Response(data, mimetype="application/json", status=200)
        except (FieldDoesNotExist, ValidationError) as e:
            print(e)
            raise SchemaValidationError
        except NotUniqueError as e:
            print(e)
            raise ItemAlreadyExistsError
        except Exception as e:
            print(e)
            raise InternalServerError


class BoardApi(Resource):
    """[Individual Board actions]
    """

    @jwt_required()
    def put(self, id):
        """[Updating single]

        Arguments:
            id {[Object ID]} -- [Mongo Object ID]

        Raises:
            SchemaValidationError: [If there are validation error in the board data]
            UpdatingItemError: [Error in update]
            InternalServerError: [Error in insertion]

        Returns:
            [json] -- [Json object with message and status code]
        """
        try:
            user_id = get_jwt_identity()
            board = Board.objects.get(id=id, added_by=user_id)
            body = request.get_json()
            Board.objects.get(id=id).update(**body)
            data = json.dumps({'message': "Successfully updated"})
            return Response(data, mimetype="application/json", status=200)
        except InvalidQueryError:
            raise SchemaValidationError
        except DoesNotExist:
            raise UpdatingItemError
        except Exception:
            raise InternalServerError

    @jwt_required()
    def delete(self, id):
        """[Deleting single board]

        Arguments:
            id {[Object ID]} -- [Mongo Object ID]

        Raises:
            DeletingItemError: [Error in deletion]
            InternalServerError: [Error in insertion]

        Returns:
            [json] -- [Json object with message and status code]
        """
        try:
            user_id = get_jwt_identity()
            board = Board.objects(slug=id, added_by=user_id)
            board.delete()
            data = json.dumps({'message': "Successfully deleted"})
            return Response(data, mimetype="application/json", status=200)
        except DoesNotExist:
            raise DeletingItemError
        except Exception as e:
            print(e)
            raise InternalServerError

    @jwt_required()
    def get(self, id):
        """[Get single board item]

        Arguments:
            id {[Object ID]} -- [Mongo Object ID]

        Raises:
            ItemNotExistsError: [Can't find the item]
            InternalServerError: [Error in insertion]

        Returns:
            [json] -- [Json object with message and status code]
        """
        try:
            user_id = get_jwt_identity()
            boards = Board.objects(slug=id, added_by=user_id).to_json()
            data = json.dumps(
                {'data': json.loads(boards), 'message': "Successfully retrieved", "count": len(json.loads(boards))})
            return Response(data, mimetype="application/json", status=200)
        except DoesNotExist:
            raise ItemNotExistsError
        except Exception:
            raise InternalServerError
