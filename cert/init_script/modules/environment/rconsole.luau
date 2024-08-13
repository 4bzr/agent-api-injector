local bridge = load_module("bridge")

local rconsole = {}

function rconsole.rconsolecreate()
    bridge:send("console_create")
    return true
end
function rconsole.rconsoledestroy()
    bridge:send("console_destroy")
    return true
end


function rconsole.rconsoleprint(msg)
    bridge:send("console_print")
    return true
end

function rconsole.rconsoleinfo(msg)
    bridge:send("console_info")
    return true
end

function rconsole.rconsolewarn(msg)
    bridge:send("console_warn")
    return true
end

function rconsole.rconsoleerr(msg)
    bridge:send("console_error")
    return true
end


function rconsole.rconsoleinput()
	local _success, result = bridge:send("console_input")

	return result
end


function rconsole.rconsoleclear()
    bridge:send("console_clear")
    return true
end

function rconsole.rconsolesettitle(title)
    bridge:send("console_title", title)
    return true
end


rconsole.consoleclear = rconsole.rconsoleclear
rconsole.consolecreate = rconsole.rconsolecreate
rconsole.consoledestroy = rconsole.rconsoledestroy
rconsole.consoleinput = rconsole.rconsoleinput
rconsole.consoleprint = rconsole.rconsoleprint
rconsole.consolename = rconsole.rconsolename

rconsole.consolesettitle = rconsole.rconsolesettitle
rconsole.rconsolename = rconsole.rconsolesettitle


return function()
    return rconsole
end