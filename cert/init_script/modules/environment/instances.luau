-- services
local run_service = game:GetService("RunService")

-- imports
local bridge = load_module("bridge")

-- objects
local hidden_ui_container = Instance.new("Folder")
hidden_ui_container.Name = "\fsavage-hui"
hidden_ui_container.RobloxLocked = true
hidden_ui_container.Parent = game:FindService("CoreGui"):FindFirstChild("RobloxGui")

-- variables
local instances_reg = setmetatable({ [game] = true }, { __mode = "ks" })
local touchers_reg = setmetatable({}, { __mode = "ks" })

-- functions
local _loaded_saveinstance

local function addToInstancesReg(descendant: Instance)
    if instances_reg[descendant] then
        return
    end
    instances_reg[descendant] = true
end

local function filterAllInstances(filter)
    local result = {}
    local idx = 1

    for instance in instances_reg do
        if not (filter(instance)) then
            continue
        end
        result[idx] = instance
        idx += 1
    end
    return result
end

-- init
game.DescendantAdded:Connect(addToInstancesReg)
game.DescendantRemoving:Connect(addToInstancesReg)

for _, instance in game:GetDescendants() do
    addToInstancesReg(instance)
end

-- main
local instance_lib = {}

-- * general instance functions

function instance_lib.getinstances()
    return filterAllInstances(function()
        return true
    end)
end

function instance_lib.getnilinstances()
    return filterAllInstances(function(instance)
        return instance.Parent == nil
    end)
end

function instance_lib.getscripts()
    return filterAllInstances(function(instance)
        return instance:IsA("LocalScript") or instance:IsA("ModuleScript")
    end)
end

function instance_lib.getmodules()
    return filterAllInstances(function(instance)
        return instance:IsA("ModuleScript")
    end)
end

-- * other instance functions

function instance_lib.gethui()
    return hidden_ui_container
end

function instance_lib.spoofinstance(spoofing: Instance, new_instance: Instance)
    assert(typeof(spoofing) == "Instance", "arg #1 must be type Instance")
    assert(typeof(new_instance) == "Instance" or type(new_instance) == "number", "arg #2 must be type Instance") -- ? or number ?
    assert(spoofing.ClassName == new_instance.ClassName, "arg #2 Instance has different ClassName to arg #1 Instance")

    task.spawn(bridge.send, bridge, "spoof_instance", spoofing, new_instance)
end

function instance_lib.getinstanceaddress(instance)
    assert(typeof(instance) == "Instance", `arg #1 must be type Instance`)

    return bridge:send("get_instance_address", instance)
end

function instance_lib.firetouchinterest(toucher: BasePart, to_touch: BasePart, touch_value: number)
    assert(typeof(toucher) == "Instance" and toucher:IsA("BasePart"), `arg #1 must be BasePart`)
    assert(typeof(to_touch) == "Instance" and to_touch:IsA("BasePart"), `arg #2 must be BasePart`)
    assert(type(touch_value) == "number", "arg #3 must be type number")

    if not touchers_reg[toucher] then
        touchers_reg[toucher] = {}
    end

    local part_address = instance_lib.getinstanceaddress(to_touch)

    if touch_value == 0 then
        if touchers_reg[toucher][part_address] then
            return
        end
        local fake_part = Instance.new(to_touch.ClassName, to_touch)
        fake_part.CanCollide = false
        fake_part.CanQuery = false
        fake_part.CanTouch = true
        fake_part.Anchored = true
        fake_part.Transparency = 1

        instance_lib.spoofinstance(fake_part, to_touch)
        touchers_reg[toucher][part_address] = true

        task.spawn(function()
            while touchers_reg[toucher][part_address] do
                fake_part.CFrame = toucher.CFrame
                task.wait()
            end

            fake_part:Destroy()
        end)
    elseif touch_value == 1 then
        if not touchers_reg[toucher][part_address] then
            return
        end

        instance_lib.spoofinstance(to_touch, part_address)
        table.remove(touchers_reg[toucher], part_address)
    end
end

function instance_lib.fireclickdetector(clickdetector, distance)
    -- TODO: do distance
    assert(typeof(clickdetector) == "Instance" and clickdetector:IsA("ClickDetector"), `arg #1 must be ClickDetector`)
    if distance ~= nil then
        assert(type(distance) == "number", `arg #2 must be type number`)
    end
    local oldCDMaxActivationDistance = clickdetector.MaxActivationDistance
    local oldCDParent = clickdetector.Parent
    local tmpPart = Instance.new("Part")
    tmpPart.Parent = workspace
    tmpPart.CanCollide = false
    tmpPart.Anchored = true
    tmpPart.Transparency = 1
    tmpPart.Size = Vector3.new(30, 30, 30)
    clickdetector.Parent = tmpPart
    --instance_lib.spoofinstance(tmpPart, clickdetector.Parent) could use it
    clickdetector.MaxActivationDistance = 9e9

    local connection
    -- credits to quiving for that one
    connection = run_service.Heartbeat:Connect(function()
        local current_camera = workspace.CurrentCamera
        tmpPart.CFrame = current_camera.CFrame
            * CFrame.new(0, 0, -20)
            * CFrame.new(current_camera.CFrame.LookVector)

        game:GetService("VirtualUser"):ClickButton1(Vector2.new(20, 20), workspace:FindFirstChildOfClass("Camera").CFrame)
    end)

    clickdetector.MouseClick:Once(function()
        connection:Disconnect()
        clickdetector.MaxActivationDistance = oldCDMaxActivationDistance
        clickdetector.Parent = oldCDParent
        tmpPart:Destroy()
    end)
end

function instance_lib.fireproximityprompt(proximityprompt, amount, skip)
    assert(
        typeof(proximityprompt) == "Instance" and proximityprompt:IsA("ProximityPrompt"),
        `arg #1 must be ProximityPrompt`
    )

    if amount ~= nil then
        assert(type(amount) == "number", `arg #2 must be type number`)
        if skip ~= nil then
            assert(type(skip) == "boolean", `arg #3 must be type boolean`)
        end
    end

    local oldHoldDuration = proximityprompt.HoldDuration
    local oldMaxDistance = proximityprompt.MaxActivationDistance

    proximityprompt.MaxActivationDistance = 9e9 -- client replicated only
    proximityprompt:InputHoldBegin()

    for i = 1, amount or 1 do -- or 1 cuz number can be nil
        if skip then
            proximityprompt.HoldDuration = 0
        else
            task.wait(proximityprompt.HoldDuration + 0.01) -- better than wait()
        end
    end

    proximityprompt:InputHoldEnd()
    proximityprompt.MaxActivationDistance = oldMaxDistance
    proximityprompt.HoldDuration = oldHoldDuration
end

function instance_lib.isnetworkowner(part)
    assert(typeof(part) == "Instance" and part:IsA("BasePart"), `arg #1 must be BasePart`)
    if part.Anchored then
        return false
    end
    return part.ReceiveAge == 0
end

function instance_lib.setsimulationradius(newRadius, newMaxRadius)
    assert(newRadius, `arg #1 is missing`)
    assert(type(newRadius) == "number", `arg #1 must be type number`)

    local LocalPlayer = game:GetService("Players").LocalPlayer
    if LocalPlayer then
        LocalPlayer.SimulationRadius = newRadius
        LocalPlayer.MaximumSimulationRadius = newMaxRadius or newRadius
    end
end

function instance_lib.saveinstance(...)
    if not _loaded_saveinstance then
        local params = {
            RepoURL = "https://raw.githubusercontent.com/luau/SynSaveInstance/main/",
            SSI = "saveinstance",
        }

        local content = instance_lib.httpget(params.RepoURL .. params.SSI .. ".luau", true)
        _loaded_saveinstance = instance_lib.loadstring(content, params.SSI)()
    end

    return _loaded_saveinstance(...)
end

function instance_lib.isscriptable(instance, property_name)
    local success, Result = xpcall(instance.GetPropertyChangedSignal, function(result)
        return result
    end, instance, property_name)

    return (success or not string.find(Result, "scriptable", nil, true))
end

function instance_lib.getproperties(instance)
    assert(typeof(instance) == "Instance", `arg #1 must be type Instance`)

    return bridge:send("get_properties", instance) -- * All, including hidden (Should be {[property_name]=value} Format)
end

function instance_lib.gethiddenproperties(instance)
    assert(typeof(instance) == "Instance", "arg #1 must be type Instance")

    local hidden_properties = {}

    -- Assuming getproperties returns an array of property names
    for _, property_name in ipairs(instance_lib.getproperties(instance)) do
        if not instance_lib.isscriptable(instance, property_name) then
            hidden_properties[property_name] = "STUB_VALUE"
        end
    end

    return hidden_properties
end

function instance_lib.gethiddenproperty(instance, property_name)
end

function instance_lib.sethiddenproperty(instance, property_name)

end


return function()
    return instance_lib,
        {
            ["getscripts"] = { "getrunningscripts" },
            ["getmodules"] = { "getloadedmodules", "getrunningmodules" },

            ["gethui"] = { "gethiddenui", "get_hidden_hui", "get_hui" },

            ["saveinstance"] = { "saveplace" },
        }
end
