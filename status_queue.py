from typing import TextIO
import queue
import json

class Rpc:
    def __init__(self):
        self.queue = queue.Queue()
    def write(
        self,
        item :str=None
    ):
        """Write an item to the queue."""
        if hasattr(self, "queue") and self.queue != None and isinstance(self.queue, queue.Queue):  # noqa: E711
            if item == None or isinstance(item, str) == False:  # noqa: E711, E712
                return
            self.queue.put(
                item=item
            )
    def read(
        self,
    ):
        """Read and remove one item from the queue."""
        if hasattr(self, "queue") and self.queue != None and isinstance(self.queue, queue.Queue):  # noqa: E711
            if not self.is_empty():
                return self.queue.get()
    def size(
        self
    ):
        """Return current queue size."""
        if hasattr(self, "queue") and self.queue != None and isinstance(self.queue, queue.Queue):  # noqa: E711
            return self.queue.qsize()
    def is_empty(
        self
    ):
        """Check if the queue is empty."""
        if hasattr(self, "queue") and self.queue != None and isinstance(self.queue, queue.Queue):  # noqa: E711
            return self.queue.empty()
    def peek(
        self
    ):
        """Peek at the next item without removing it."""
        # No indexing, instead replacing it with snapshot
        # if not self.is_empty():
        #     item = await self.read()
        #     await self.write(
        #         item=item
        #     )
        #     return item
        if not self.is_empty():
            items = self.snapshot()
            if items != None and isinstance(items, list):  # noqa: E711
                if items.__len__() > 0:
                    return items[0]
    def drain(
        self
    ):
        """Remove and return all items from the queue."""
        items = []
        while not self.is_empty():
            items.append(self.read())
        return items
    def snapshot(
        self
    ):
        """Return a snapshot of the queue contents without removing them."""
        if not self.is_empty():
            items = []
            for _ in range(self.size()):
                item = self.read()
                items.append(item)
                self.write(
                    item=item
                )
            return items
    def clear(
        self
    ):
        """Clear all items in the queue."""
        self.drain()
    def dump(
        self,
        fp :TextIO=None
    ):
        """Write queue contents to a file, one per line."""
        if fp == None or isinstance(fp, TextIO) == False:  # noqa: E711, E712
            return
        fp.write(
            s=self.dumps()
        )
    def dumps(
        self
    ):
        """Return queue contents as a string with one item per line."""
        return "\n".join(str(item) for item in self.snapshot())
    def load(
        self,
        fp :TextIO=None
    ):
        """Load items into the queue from a text file (one item per line)."""
        if fp == None or isinstance(fp, TextIO) == False:  # noqa: E711, E712
            return
        for line in fp.readlines():
            self.write(
                item=line.strip()
            )
    def loads(
        self,
        data :str=None
    ):
        """Load items into the queue from a string (one item per line)."""
        if data == None or isinstance(data, str) == False:  # noqa: E711, E712
            return
        for line in data.splitlines():
            self.write(
                item=line.strip()
            ) 
    def dump_snapshot_json(
        self,
        fp :TextIO=None,
        indent :int=None
    ):
        """Write the queue to a file in JSON format."""
        if fp == None or isinstance(fp, TextIO) == False:  # noqa: E711, E712
            return
        json.dump(
            fp=fp,
            obj=self.snapshot(),
            indent=indent
        )
    def dumps_snapshot_json(
        self,
        indent :int=None
    ):
        """Return the queue as a JSON string."""
        return json.dumps(
            obj=self.snapshot(),
            indent=indent
        )
    def load_snapshot_json(
        self,
        fp: TextIO = None
    ):
        """Load items into the queue from a JSON file (expects a list)."""
        if fp == None or isinstance(fp, TextIO) == False:  # noqa: E711, E712
            return
        data = json.load(
            fp=fp
        )
        if data == None or isinstance(data, list) == False:  # noqa: E711, E712
            return
        for item in data:
            self.write(
                item=data
            )
    def loads_snapshot_json(
        self,
        data :str=None
    ):
        """Load items into the queue from a JSON string (expects a list)."""
        for item in json.loads(
            s=data
        ):
            self.write(
                item=data
            )
    def write_bulk(
        self,
        items :list=None
    ):
        """Write multiple items into the queue."""
        if items == None or isinstance(items, list) == False:  # noqa: E711, E712
            return
        for item in items:
            self.write(
                item=item
            )
    def read_bulk(
        self, 
        n :int=None
    ):
        """Read up to n items from the queue."""
        if n == None or isinstance(n, int) == False:  # noqa: E711, E712
            return
        results = []
        for _ in range(min(n, self.size())):
            results.append(self.read())
        return results