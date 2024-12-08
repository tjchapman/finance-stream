import avro.io
from io import BytesIO


def avro_decode(message_value, schema):
    """
    Decodes message from avro binary format
    """
    reader = avro.io.DatumReader(schema)
    message_bytes = BytesIO(message_value)
    # message_bytes.seek(5)
    decoder = avro.io.BinaryDecoder(message_bytes)
    event_dict = reader.read(decoder)
    return event_dict
