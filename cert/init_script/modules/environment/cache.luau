local cache = {}
local script_env

local CloneRefs = { Clones = setmetatable({}, { __mode = "ks" }), Originals = setmetatable({}, { __mode = "vs" }) }

local function ReturnOriginal(instance)
    local CloneInfo = CloneRefs.Clones[instance]
    if CloneInfo then
        return CloneInfo.Original
    end
end

function cache.cloneref(instance)
    local Original = ReturnOriginal(instance)
    if Original then
        instance = Original
    end

    local Clone = newproxy(true)
    local Mt_Clone = getmetatable(Clone)
    local Mt_Real = script_env.getrawmetatable(instance)

    local CloneInfo = CloneRefs.Originals[instance]
    if not CloneInfo then
        CloneInfo = { Original = instance, __type = Mt_Real.__type }
        CloneRefs.Originals[instance] = CloneInfo
    end

    CloneRefs.Clones[Clone] = CloneInfo

    for Metamethod, Value in Mt_Real do
        Mt_Clone[Metamethod] = type(Value) == "function"
                and function(self, ...)
                    return Value(instance, ...)
                end
            or Value
    end

    return Clone
end

function cache.compareinstances(instance, instance2)
    local CloneInfo = CloneRefs.Clones[instance]
    local CloneInfo2 = CloneRefs.Clones[instance2]
    if CloneInfo then
        instance = CloneInfo.Original
    end
    if CloneInfo2 then
        instance2 = CloneInfo2.Original
    end

    return instance == instance2
end

return function(_script_env)
    script_env = _script_env
    return cache
end
