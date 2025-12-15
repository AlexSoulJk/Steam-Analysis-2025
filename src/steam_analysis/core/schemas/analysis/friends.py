from typing import List, Union

from steam_analysis.core.schemas.base import BaseSchema


class NodeBase(BaseSchema):
    id: Union[int, str]
    name: str
    type: str


class NodeWithCount(NodeBase):
    count: int


class OrtBase(BaseSchema):
    source: str
    target: str


class FriendsByGames(BaseSchema):
    nodes: List[Union[NodeBase, NodeWithCount]]
    orts: List[OrtBase]
