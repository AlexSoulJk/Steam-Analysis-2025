from typing import List, Union

from steam_analysis.core.schemas.base import BaseSchema


class NodeBase(BaseSchema):
    id: Union[int, str]
    name: str
    type: str


class NodeUser(NodeBase):
    steam_id: str
    url: str


class NodeWithCount(NodeBase):
    count: int


class NodeGame(NodeWithCount):
    app_id: str


class OrtBase(BaseSchema):
    source: str
    target: str


class FriendsByGames(BaseSchema):
    nodes: List[Union[NodeUser, NodeGame]]
    orts: List[OrtBase]
