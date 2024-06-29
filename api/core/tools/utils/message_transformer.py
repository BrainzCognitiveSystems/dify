import logging
from mimetypes import guess_extension

from core.file.file_obj import FileTransferMethod, FileType, FileVar
from core.tools.entities.tool_entities import ToolInvokeMessage
from core.tools.tool_file_manager import ToolFileManager

logger = logging.getLogger(__name__)

class ToolFileMessageTransformer:
    @classmethod
    def transform_tool_invoke_messages(cls, messages: list[ToolInvokeMessage],
                                       user_id: str,
                                       tenant_id: str,
                                       conversation_id: str) -> list[ToolInvokeMessage]:
        """
        Transform tool message and handle file download
        """
        result = []

        for message in messages:
            if message.type == ToolInvokeMessage.MessageType.TEXT:
                result.append(message)
            elif message.type == ToolInvokeMessage.MessageType.LINK:
                result.append(message)
            elif message.type == ToolInvokeMessage.MessageType.JSON:
                img_tag = message.message.get('_image')
                if img_tag:
                    img_url = img_tag.split(':', 1)[1]
                    msg_img = ToolInvokeMessage(type=ToolInvokeMessage.MessageType.IMAGE, message=img_url)
                    msg_img = ToolFileMessageTransformer.transform_tool_invoke_messages([msg_img], user_id, tenant_id, conversation_id)[0]
                    result.append(msg_img)
                    message.message['_file__remote_url'] = msg_img.message
                result.append(message)
            elif message.type == ToolInvokeMessage.MessageType.IMAGE:
                # try to download image
                file_url1=message.message
                file_url2="https:"+file_url1[5:] if file_url1.startswith('http:') else "http:"+file_url1[6:]
                success = False
                for file_url in [file_url1, file_url2]:
                    try:
                        file = ToolFileManager.create_file_by_url(
                            user_id=user_id,
                            tenant_id=tenant_id,
                            conversation_id=conversation_id,
                            file_url=file_url
                        )

                        url = cls.get_tool_file_url(file.id, guess_extension(file.mimetype))

                        result.append(ToolInvokeMessage(
                            type=ToolInvokeMessage.MessageType.IMAGE_LINK,
                            message=url,
                            save_as=message.save_as,
                            meta=message.meta.copy() if message.meta is not None else {},
                        ))
                        success = True
                        break
                    except Exception as e:
                        logger.exception(e)
                if not success:
                    result.append(ToolInvokeMessage(
                        type=ToolInvokeMessage.MessageType.TEXT,
                        message=f"Failed to download image: {message.message}, you can try to download it yourself.",
                        meta=message.meta.copy() if message.meta is not None else {},
                        save_as=message.save_as,
                    ))
            elif message.type == ToolInvokeMessage.MessageType.BLOB:
                # get mime type and save blob to storage
                mimetype = message.meta.get('mime_type', 'octet/stream')
                # if message is str, encode it to bytes
                if isinstance(message.message, str):
                    message.message = message.message.encode('utf-8')
                
                file = ToolFileManager.create_file_by_raw(
                    user_id=user_id, tenant_id=tenant_id,
                    conversation_id=conversation_id,
                    file_binary=message.message,
                    mimetype=mimetype
                )
                                                            
                url = cls.get_tool_file_url(file.id, guess_extension(file.mimetype))

                # check if file is image
                if 'image' in mimetype:
                    result.append(ToolInvokeMessage(
                        type=ToolInvokeMessage.MessageType.IMAGE_LINK,
                        message=url,
                        save_as=message.save_as,
                        meta=message.meta.copy() if message.meta is not None else {},
                    ))
                else:
                    result.append(ToolInvokeMessage(
                        type=ToolInvokeMessage.MessageType.LINK,
                        message=url,
                        save_as=message.save_as,
                        meta=message.meta.copy() if message.meta is not None else {},
                    ))
            elif message.type == ToolInvokeMessage.MessageType.FILE_VAR:
                file_var: FileVar = message.meta.get('file_var')
                if file_var:
                    if file_var.transfer_method == FileTransferMethod.TOOL_FILE:
                        url = cls.get_tool_file_url(file_var.related_id, file_var.extension)
                        if file_var.type == FileType.IMAGE:
                            result.append(ToolInvokeMessage(
                                type=ToolInvokeMessage.MessageType.IMAGE_LINK,
                                message=url,
                                save_as=message.save_as,
                                meta=message.meta.copy() if message.meta is not None else {},
                            ))
                        else:
                            result.append(ToolInvokeMessage(
                                type=ToolInvokeMessage.MessageType.LINK,
                                message=url,
                                save_as=message.save_as,
                                meta=message.meta.copy() if message.meta is not None else {},
                            ))
            else:
                result.append(message)

        return result
    
    @classmethod
    def get_tool_file_url(cls, tool_file_id: str, extension: str) -> str:
        return f'/files/tools/{tool_file_id}{extension or ".bin"}'