import types


# 添加ModuleFather
class ModuleFather:
    sdk = types.SimpleNamespace()


# 外部sdk对象指向ModuleFather
sdk = ModuleFather.sdk
setattr(sdk, 'ModuleFather', ModuleFather)

sdk.ModuleFather.sdk.aaaaa = 123

print(ModuleFather.sdk.aaaaa)