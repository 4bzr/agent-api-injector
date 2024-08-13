local bridge = load_module("bridge")

local script_env

local scripts = {}

function scripts.getscriptbytecode(instance)
    assert(typeof(instance) == "Instance" and instance:IsA("LuaSourceContainer"), `arg #1 must be LuaSourceContainer`)

    local success, bytecode = bridge:send("get_script_bytecode", instance)
    if not success then
        return error(`Failed to get bytecode of '{instance:GetFullName()}'`, 2)
    end

    return bytecode
end

-- broken ass decompile
--function scripts.decompile(x)
--    local disassemble = script_env.loadstring(script_env.httpget("https://raw.githubusercontent.com/TheSeaweedMonster/Lua-Scripts/main/decompile.lua"))()
--    return disassemble(x)
--end

function scripts.getscripthash(instance) -- TODO Replace by sha384(getscriptbytecode(instance)) later, current impl is bad
    assert(typeof(instance) == "Instance" and instance:IsA("LuaSourceContainer"), `arg #1 must be LuaSourceContainer`)

    return if instance:IsA("Script") then instance:GetHash() else instance:GetDebugId(0)
end

function scripts.getscriptclosurefunction()

end

function scripts.setscriptable()

end

function scripts.getscriptfunction()
    
end

function scripts.getexecutioncontext()
    local RunService = game:GetService("RunService")

    return if RunService:IsClient()
        then "Client"
        elseif RunService:IsServer() then "Server"
        else if RunService:IsStudio() then "Studio" else "Unknown"
end

function scripts.isluau()
    return _VERSION == "Luau"
end

function scripts.stringdump(func)
    local funcString = tostring(func)

    return bridge:send("python_string_dump", funcString)
end

return function(_script_env)
    script_env = _script_env
    return scripts,
        { 
            ["getscriptbytecode"] = { "dumpstring" },
            ["stringdump2"] = stringdump,
        }
end
