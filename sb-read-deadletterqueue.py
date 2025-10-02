import os
from azure.servicebus import ServiceBusClient, ServiceBusMessage, ServiceBusSubQueue
from azure.identity import DefaultAzureCredential

#FULLY_QUALIFIED_NAMESPACE = os.environ["SERVICEBUS_FULLY_QUALIFIED_NAMESPACE"]
CONN_STR = os.environ["SERVICEBUS_CONNECTION_STRING"]
QUEUE_NAME = os.environ["SERVICEBUS_QUEUE_NAME"]

print(f'CONN_STR: ${CONN_STR}')
print(f'QUEUE_NAME: ${QUEUE_NAME}')

servicebus_client = ServiceBusClient.from_connection_string(CONN_STR)

with servicebus_client:
    sender = servicebus_client.get_queue_sender(queue_name=QUEUE_NAME)
    #messages = [ServiceBusMessage("Message to be deadlettered") for _ in range(10)]
    #with sender:
    #    sender.send_messages(messages)

    #print("dead lettering messages")
    #receiver = servicebus_client.get_queue_receiver(queue_name=QUEUE_NAME)
    #with receiver:
    #    received_msgs = receiver.receive_messages(max_message_count=10, max_wait_time=5)
    #    for msg in received_msgs:
    #        print(str(msg))
    #        receiver.dead_letter_message(msg)

    print("receiving deadlettered message")
    dlq_receiver = servicebus_client.get_queue_receiver(queue_name=QUEUE_NAME, sub_queue=ServiceBusSubQueue.DEAD_LETTER)
    with dlq_receiver:
        received_msgs = dlq_receiver.receive_messages(max_message_count=50, max_wait_time=5)
        for msg in received_msgs:
            print(str(msg))
            sender.send_messages(msg)
            dlq_receiver.complete_message(msg)

print("Receive is done")