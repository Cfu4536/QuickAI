from tools import hash_encrypt

device_id = input("请输入设备ID：")
encrypted_str = hash_encrypt(device_id)
print(f"序列号为：{encrypted_str}")


