local setthread = {}

changedidentity = false

local thread = {}

thread.thread_identity = 1356

function setthreadidentity(identity)
    changedidentity = true
    thread.thread_identity = identity
end

function getthreadidentity()
    if changedidentity == true then
        return thread.thread_identity
    end

    local function try(fn, ...)
        local o = pcall(fn, ...)
        return o
    end

    local ourresults = {
        -- ! ITS IMPORTANT WE DONT USE ANY METHODS HERE THAT WE SPOOF
        -- ! HOPEFULLY Security Tags of these dont change
        -- PluginSecurity (1)
        try(function()
            return game:GetJobsInfo()
        end),
        -- LocalUserSecurity (3)
        try(function()
            return workspace:ExperimentalSolverIsEnabled()
        end),
        --WritePlayerSecurity (4)
        try(Instance.new, "Player"),
        --RobloxScriptSecurity (5)
        try(function()
            return game:GetPlaySessionId()
        end),
        --RobloxSecurity (6)
        try(function()
            return Instance.new("SurfaceAppearance").TexturePack
        end),
        --NotAccessibleSecurity (7)
        try(function()
            Instance.new("MeshPart").HasJointOffset = false
        end),
    }
    local permissionChart =
        { -- We go in reverse because LocalGui is equal to CommandBar in permissionChart it seems like (this way we can match properly, though we can't tell lvl 7 from 8 then but not like that's a big issue)
            { true, true, false, false, false, false }, -- LocalGui [1]
            { false, false, false, false, false, false }, -- GameScript [2]
            { true, true, false, true, false, false }, -- ElevatedGameScript [3]
            { true, true, false, false, false, false }, -- CommandBar [4]
            { true, false, false, false, false, false }, -- StudioPlugin [5]
            { true, true, false, true, false, false }, -- ElevatedStudioPlugin [6]
            { true, true, true, true, true, true }, -- COM [7] Level 7 WOOHOO
            { true, true, true, true, true, true }, -- WebService [8] WOW LVL 8
            { false, false, true, true, false, false }, -- Replicator [9]
        }

    for level = #permissionChart, 1, -1 do
        local securityInfo = permissionChart[level]

        local match = true
        for i, canAccess in securityInfo do
            if canAccess ~= ourresults[i] then
                match = false
                break
            end
        end
        if match then
            return level
        end
    end
    return 0
end

return function()
    return {
        setthreadcontext = setthreadidentity,
        setidentity = setthreadidentity,
        setthreadidentity = setthreadidentity,
        getthreadidentity = getthreadidentity,
        getidentity = getthreadidentity,
        getthreadcontext = getthreadidentity,
    }
end