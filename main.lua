local function test()
	
	file = io.open(mp.get_script_directory() .. "/settings.txt", "w")
	ipc_handle_path = mp.get_property('input-ipc-server')
	
	if ipc_handle_path == '' or ipc_handle_path == nil then
        local new_ipc_handle_path = '/tmp/mpv-ipc-handle-' .. os.time()
        mp.set_property('input-ipc-server', new_ipc_handle_path)
        ipc_handle_path = mp.get_property('input-ipc-server')
    end
	
	file:write(ipc_handle_path)
	file:close()
	
	mp.commandv("run", "python3", mp.get_script_directory() .. '/mpv_pauser.py')
	
end

test()