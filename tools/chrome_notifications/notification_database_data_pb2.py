# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: notification_database_data.proto
# Protobuf Python Version: 4.25.1
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n notification_database_data.proto\"\xff\t\n\x1dNotificationDatabaseDataProto\x12\"\n\x1apersistent_notification_id\x18\x01 \x01(\x03\x12\x17\n\x0fnotification_id\x18\x05 \x01(\t\x12\x0e\n\x06origin\x18\x02 \x01(\t\x12&\n\x1eservice_worker_registration_id\x18\x03 \x01(\x03\x12&\n\x1ereplaced_existing_notification\x18\x06 \x01(\x08\x12\x12\n\nnum_clicks\x18\x07 \x01(\x05\x12 \n\x18num_action_button_clicks\x18\x08 \x01(\x05\x12\x1c\n\x14\x63reation_time_millis\x18\t \x01(\x03\x12%\n\x1dtime_until_first_click_millis\x18\n \x01(\x03\x12$\n\x1ctime_until_last_click_millis\x18\x0b \x01(\x03\x12\x1f\n\x17time_until_close_millis\x18\x0c \x01(\x03\x12\x42\n\rclosed_reason\x18\r \x01(\x0e\x32+.NotificationDatabaseDataProto.ClosedReason\x12J\n\x11notification_data\x18\x04 \x01(\x0b\x32/.NotificationDatabaseDataProto.NotificationData\x12\x15\n\rhas_triggered\x18\x0e \x01(\x08\x1a\xba\x01\n\x12NotificationAction\x12\x0e\n\x06\x61\x63tion\x18\x01 \x01(\t\x12\r\n\x05title\x18\x02 \x01(\t\x12\x0c\n\x04icon\x18\x03 \x01(\t\x12\x44\n\x04type\x18\x04 \x01(\x0e\x32\x36.NotificationDatabaseDataProto.NotificationAction.Type\x12\x13\n\x0bplaceholder\x18\x05 \x01(\t\"\x1c\n\x04Type\x12\n\n\x06\x42UTTON\x10\x00\x12\x08\n\x04TEXT\x10\x01\x1a\xe4\x03\n\x10NotificationData\x12\r\n\x05title\x18\x01 \x01(\t\x12L\n\tdirection\x18\x02 \x01(\x0e\x32\x39.NotificationDatabaseDataProto.NotificationData.Direction\x12\x0c\n\x04lang\x18\x03 \x01(\t\x12\x0c\n\x04\x62ody\x18\x04 \x01(\t\x12\x0b\n\x03tag\x18\x05 \x01(\t\x12\r\n\x05image\x18\x0f \x01(\t\x12\x0c\n\x04icon\x18\x06 \x01(\t\x12\r\n\x05\x62\x61\x64ge\x18\x0e \x01(\t\x12\x1d\n\x11vibration_pattern\x18\t \x03(\x05\x42\x02\x10\x01\x12\x11\n\ttimestamp\x18\x0c \x01(\x03\x12\x10\n\x08renotify\x18\r \x01(\x08\x12\x0e\n\x06silent\x18\x07 \x01(\x08\x12\x1b\n\x13require_interaction\x18\x0b \x01(\x08\x12\x0c\n\x04\x64\x61ta\x18\x08 \x01(\x0c\x12\x42\n\x07\x61\x63tions\x18\n \x03(\x0b\x32\x31.NotificationDatabaseDataProto.NotificationAction\x12\x1e\n\x16show_trigger_timestamp\x18\x10 \x01(\x03\";\n\tDirection\x12\x11\n\rLEFT_TO_RIGHT\x10\x00\x12\x11\n\rRIGHT_TO_LEFT\x10\x01\x12\x08\n\x04\x41UTO\x10\x02\"4\n\x0c\x43losedReason\x12\x08\n\x04USER\x10\x00\x12\r\n\tDEVELOPER\x10\x01\x12\x0b\n\x07UNKNOWN\x10\x02')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'notification_database_data_pb2', _globals)
if _descriptor._USE_C_DESCRIPTORS == False:
  DESCRIPTOR._options = None
  _globals['_NOTIFICATIONDATABASEDATAPROTO_NOTIFICATIONDATA'].fields_by_name['vibration_pattern']._options = None
  _globals['_NOTIFICATIONDATABASEDATAPROTO_NOTIFICATIONDATA'].fields_by_name['vibration_pattern']._serialized_options = b'\020\001'
  _globals['_NOTIFICATIONDATABASEDATAPROTO']._serialized_start=37
  _globals['_NOTIFICATIONDATABASEDATAPROTO']._serialized_end=1316
  _globals['_NOTIFICATIONDATABASEDATAPROTO_NOTIFICATIONACTION']._serialized_start=589
  _globals['_NOTIFICATIONDATABASEDATAPROTO_NOTIFICATIONACTION']._serialized_end=775
  _globals['_NOTIFICATIONDATABASEDATAPROTO_NOTIFICATIONACTION_TYPE']._serialized_start=747
  _globals['_NOTIFICATIONDATABASEDATAPROTO_NOTIFICATIONACTION_TYPE']._serialized_end=775
  _globals['_NOTIFICATIONDATABASEDATAPROTO_NOTIFICATIONDATA']._serialized_start=778
  _globals['_NOTIFICATIONDATABASEDATAPROTO_NOTIFICATIONDATA']._serialized_end=1262
  _globals['_NOTIFICATIONDATABASEDATAPROTO_NOTIFICATIONDATA_DIRECTION']._serialized_start=1203
  _globals['_NOTIFICATIONDATABASEDATAPROTO_NOTIFICATIONDATA_DIRECTION']._serialized_end=1262
  _globals['_NOTIFICATIONDATABASEDATAPROTO_CLOSEDREASON']._serialized_start=1264
  _globals['_NOTIFICATIONDATABASEDATAPROTO_CLOSEDREASON']._serialized_end=1316
# @@protoc_insertion_point(module_scope)
