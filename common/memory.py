from common.expired_dict import ExpiredDict
# 带有过期时间的缓存
USER_IMAGE_CACHE = ExpiredDict(60 * 3)