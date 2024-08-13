-- imports
local bridge = load_module("bridge")

local script_env

-- main
local misc = {}

misc.isreadonly = table.isfrozen

function misc.identifyexecutor()
    return "${EXEC_AUTOMATIC}", "${VERSION_AUTOMATIC}"
end

function misc.setclipboard(to_copy)
    assert(type(to_copy) == "string", `arg #1 must be type string`)
    assert(to_copy ~= "", `arg #1 cannot be empty`)

    local clipboard_success = bridge:send("set_clipboard", to_copy)

    if not clipboard_success then
        return error("Can't set to clipboard", 2)
    end
    return clipboard_success
end

function misc.queueonteleport()
    
end

function misc.getobjects(assetid)
    if type(assetid) == "number" then
        assetid = "rbxassetid://" .. assetid
    end
    return { game:GetService("InsertService"):LoadLocalAsset(assetid) }
end

function misc.getcustomasset(path)
    assert(path ~= "", `arg #1 cannot be empty`)
    assert(type(path) == "string", `arg #1 must be type string`)

    local backslashed_path = string.gsub(path, "/", "\\")
    local success, asset_url = bridge:send("get_custom_asset", backslashed_path)

    if not success then
        return error(`Failed to get asset URL of '{path}'`, 2)
    end
    return asset_url
end

function misc.messagebox(text, caption, flags)
    assert(type(text) == "string", `arg #1 must be type string`)
    assert(text ~= "", `arg #1 cannot be empty`)
    assert(type(caption) == "string", `arg #2 must be type string`)
    assert(caption ~= "", `arg #2 cannot be empty`)
    if flags ~= nil then
        assert(type(flags) == "number", `arg #3 should be a number`)
    end

    local _success, result = bridge:send("messagebox", text, caption, flags or 1)

    return result
end

function misc.gethwid()
    local success, hwid = bridge:send("get_hwid")
    if not success then
        return error("Failed to get HWID", 2)
    end
    return hwid
end


misc.setrawmetatable = function(object, newmetatable)
    -- Store the new metatable on the object itself
    object.__rawmetatable = newmetatable
    
    -- Override the object's index behavior
    local oldIndex = object.__index
    object.__index = function(t, k)
        if newmetatable.__index then
            return newmetatable.__index(t, k)
        elseif oldIndex then
            return oldIndex(t, k)
        end
    end
    
    -- Return the original object
    return object
end

misc.getcallbackvalue = function(object, property)
    assert(typeof(object) == "Instance", "First argument must be an Instance")
    assert(type(property) == "string", "Second argument must be a string")

    -- Check if the property exists and is a callback
    local success, result = pcall(function()
        return object[property]
    end)

    if success and type(result) == "function" then
        return result
    else
        return nil
    end
end

misc.getconnections = function(event)
    assert(typeof(event) == "RBXScriptSignal", "Argument must be a RBXScriptSignal")

    local connections = {}

    -- Create a dummy connection to get the internal connection object
    local dummyConnection = event:Connect(function() end)
    
    -- Create a table with the required fields
    local connectionInfo = {
        Enabled = true,
        ForeignState = false,
        LuaConnection = true,
        Function = function() end,
        Thread = coroutine.create(function() end),
        Fire = function() dummyConnection:Fire() end,
        Defer = function() task.defer(dummyConnection.Fire, dummyConnection) end,
        Disconnect = function() dummyConnection:Disconnect() end,
        Disable = function() connectionInfo.Enabled = false end,
        Enable = function() connectionInfo.Enabled = true end,
    }

    table.insert(connections, connectionInfo)

    -- Clean up the dummy connection
    dummyConnection:Disconnect()

    return connections
end



function misc.getfflag(flag)
    assert(type(flag) == "string", "arg #1 must be type string")
    assert(flag ~= "", `arg #1 cannot be empty`)

    for container, methods in
        { [game] = { "GetFastFlag", "GetFastString", "GetFastInt" }, [settings()] = { "GetFFlag", "GetFVariable" } }
    do
        for _, method in methods do
            local s, r = pcall(container[method], container, flag)
            if s then
                return r
            end
        end
    end
end

do -- TODO Should be able to uncap
    local RunService = game:GetService("RunService")
    local Capped, FractionOfASecond
    local Heartbeat = RunService.Heartbeat
    function misc.setfpscap(fps_cap)
        if fps_cap == 0 or fps_cap == nil or 1e4 <= fps_cap then -- ~7k fps is the highest people have gotten; --?maybe compare to getfpsmax instead? (but we have to ensure getfpsmax is accurate first)
            if Capped then
                task.cancel(Capped)
                Capped = nil
                FractionOfASecond = nil
            end
            return
        end

        FractionOfASecond = 1 / fps_cap
        if Capped then
            return
        end
        local function Capper()
            -- * Modified version of https://github.com/MaximumADHD/Super-Nostalgia-Zone/blob/540221bc945a8fc3a45baf51b40e02272a21329d/Client/FpsCap.client.lua#
            local t0 = os.clock()
            Heartbeat:Wait()
            -- repeat until t0 + t1 < tick()
            -- local count = 0
            while os.clock() <= t0 + FractionOfASecond do -- * not using repeat to avoid unreasonable extra iterations
                -- count+=1
            end
            -- task.spawn(print,count)
        end
        Capper() -- Yield until it kicks in basically
        Capped = task.spawn(function()
            -- capping = true -- * this works too
            while true do
                Capper()
            end
        end)
    end
end

misc.getgc = function()
    local function scanTable(t, scanned)
        if scanned[t] then return end
        scanned[t] = true
    
        for k, v in pairs(t) do
            if type(v) == "table" then
                scanTable(v, scanned)
            end
        end
    end

    local scanned = {}
    local results = {}

    scanTable(_G, scanned)

    for t in pairs(scanned) do
        table.insert(results, t)
    end

    return results
end



function misc.hookfunction(old, new, run_on_seperate_thread)
   local Metatable_library = {
       metamethods = {
           __index = function(self, key)
               return self[key]
           end,
           __newindex = function(self, key, value)
               self[key] = value
           end,
           __call = function(self, ...)
               return self(...)
           end,
       }
   }
    
   function Metatable_library.metahook(t, f)
       local metahook = {
           __metatable = getmetatable(t) or "The metatable is locked"
       }
    
       for metamethod, value in pairs(Metatable_library.metamethods) do
           metahook[metamethod] = function(self, ...)
               f()
               return Metatable_library.metahook({}, f)
           end
       end
    
       return setmetatable({}, metahook)
   end

   local is_jammable = pcall(setfenv, old, getfenv(old))
    
   if not is_jammable then
       local name = debug.getinfo(old, "n").name
        
       if getfenv(old)[name] == old then
           getfenv(old)[name] = new
       else
           error("Unable to hook local C closures", 0)
       end
   else
       local old_environment = getfenv(old)
       
       local last_line = -1
       local last_source = function() end
       
       local debug_info = debug.getinfo
       local hook = Metatable_library.metahook(getfenv(old), function()
           local line, source = debug_info(4, "ls")

           if line ~= last_line or last_source ~= last_source then
               if new then
                   if run_on_seperate_thread then
                       task.spawn(function()
                           pcall(function()
                               coroutine.wrap(pcall)(new)
                           end)
                       end)
                   else
                       new()
                   end
               end

               last_line = line
               last_source = source
           end
       end)
        
       for i, v in pairs(old_environment) do
           rawset(hook, i, v)
       end
        
       setfenv(old, hook)
        
       return function(...)
           local return_value = {setfenv(old, old_environment)(...)}
           setfenv(old, hook)
            
           return unpack(return_value)
       end
   end
end




-- Cache lib

misc.cache = {}
cache = {}

function misc.cache.iscached(thing)
    if not thing.Parent then
        return cache[thing] ~= 'REMOVE'
    else
        return false
    end
end

function misc.cache.invalidate(thing)
    cache[thing] = 'REMOVE'
    thing.Parent = nil
end

function misc.cache.replace(a, b)
    if cache[a] then
        cache[a] = b
    end
end

do -- Websockets
    local WebSocket = { connect = nil }

    local websocket_mt = {
        __index = function(self, index)
            if not rawget(self, "__OBJECT_ACTIVE") then
                error("WebSocket is closed.")
            end

            if index == "OnMessage" then
                if not rawget(self, "__OBJECT_ACTIVE") then
                    error("WebSocket is closed.")
                end

                return rawget(self, "__OBJECT_MESSAGE")
            end

            if index == "OnClose" then
                if not rawget(self, "__OBJECT_ACTIVE") then
                    error("WebSocket is closed.")
                end

                return rawget(self, "__OBJECT_CLOSE")
            end

            if index == "Send" then
                return function(_, message, is_binary)
                    if not rawget(self, "__OBJECT_ACTIVE") then
                        error("WebSocket is closed.")
                    end

                    bridge:send("websocket_send", rawget(self, "__OBJECT"), message, is_binary)
                end
            end

            if index == "Close" then
                return function(_)
                    if not rawget(self, "__OBJECT_ACTIVE") then
                        error("WebSocket is closed.")
                    end
                    rawset(self, "__OBJECT_ACTIVE", false)

                    bridge:send("websocket_close", rawget(self, "__OBJECT"))
                end
            end
        end,
        __newindex = function()
            error("WebSocket is readonly.")
        end,
        __type = "WebSocket",
    }

    function WebSocket.connect(url: string)
        -- TODO: This might break (mix up) if called quickly within a short time span

        local success = bridge:send("websocket_connect", url)
        if not success then
            error("Failed to start/connect WebSocket server", 2)
        end

        local websocket_connection = setmetatable({
            ClassName = "WebSocket",
            __OBJECT = url,
            __OBJECT_ACTIVE = true,
            __OBJECT_MESSAGE = goodsignal.new(),
            __OBJECT_CLOSE = goodsignal.new(),
        }, websocket_mt)

        websocket_connection.__OBJECT_CLOSE:Connect(function()
            websocket_connection.__OBJECT_ACTIVE = false
        end)

        game:GetService("Players").LocalPlayer.OnTeleport:Connect(function(teleportState)
            if teleportState == Enum.TeleportState.Started and websocket_connection.__OBJECT_ACTIVE then
                websocket_connection:Close()
            end
        end)

        bridge:register_callback(url .. "_message", function(...)
            websocket_connection.__OBJECT_MESSAGE:Fire(...)
        end)

        bridge:register_callback(url .. "_close", function(...)
            websocket_connection.__OBJECT_CLOSE:Fire(...)
        end)

        return websocket_connection
    end

    misc.WebSocket = WebSocket
end




return function(_script_env)
    script_env = _script_env
    return misc,
        {
            ["getthreadidentity"] = { "getidentity", "getthreadcontext" },
            ["identifyexecutor"] = { "getexecutorname", "whatexecutor" },
            ["setclipboard"] = { "toclipboard" },
            ["setrawmetatable"] = {},
            
            
        }
end