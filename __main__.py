"""
Initializes queue database
"""
import persistqueue

queue = persistqueue.UniqueAckQ("txs", auto_commit=True)

def main():
    queue.put("init")
    item = queue.get()
    queue.ack(item)

if __name__ == "__main__":
    main()