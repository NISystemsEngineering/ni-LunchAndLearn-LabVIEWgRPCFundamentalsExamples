<?xml version='1.0' encoding='UTF-8'?>
<Project Type="Project" LVVersion="25008000">
	<Property Name="NI.LV.All.SaveVersion" Type="Str">25.0</Property>
	<Property Name="NI.LV.All.SourceOnly" Type="Bool">true</Property>
	<Item Name="My Computer" Type="My Computer">
		<Property Name="IOScan.Faults" Type="Str"></Property>
		<Property Name="IOScan.NetVarPeriod" Type="UInt">100</Property>
		<Property Name="IOScan.NetWatchdogEnabled" Type="Bool">false</Property>
		<Property Name="IOScan.Period" Type="UInt">10000</Property>
		<Property Name="IOScan.PowerupMode" Type="UInt">0</Property>
		<Property Name="IOScan.Priority" Type="UInt">9</Property>
		<Property Name="IOScan.ReportModeConflict" Type="Bool">true</Property>
		<Property Name="IOScan.StartEngineOnDeploy" Type="Bool">false</Property>
		<Property Name="server.app.propertiesEnabled" Type="Bool">true</Property>
		<Property Name="server.control.propertiesEnabled" Type="Bool">true</Property>
		<Property Name="server.tcp.enabled" Type="Bool">false</Property>
		<Property Name="server.tcp.port" Type="Int">0</Property>
		<Property Name="server.tcp.serviceName" Type="Str">My Computer/VI Server</Property>
		<Property Name="server.tcp.serviceName.default" Type="Str">My Computer/VI Server</Property>
		<Property Name="server.vi.callsEnabled" Type="Bool">true</Property>
		<Property Name="server.vi.propertiesEnabled" Type="Bool">true</Property>
		<Property Name="specify.custom.address" Type="Bool">false</Property>
		<Item Name="Libraries" Type="Folder">
			<Item Name="Linux" Type="Folder">
				<Item Name="liblabview_grpc_server.so" Type="Document" URL="/&lt;vilib&gt;/gRPC/LabVIEW gRPC Library/Libraries/Linux/liblabview_grpc_server.so"/>
			</Item>
			<Item Name="LinuxRT" Type="Folder">
				<Item Name="liblabview_grpc_server.so" Type="Document" URL="/&lt;vilib&gt;/gRPC/LabVIEW gRPC Library/Libraries/LinuxRT/liblabview_grpc_server.so"/>
			</Item>
			<Item Name="Win32" Type="Folder">
				<Item Name="labview_grpc_server.dll" Type="Document" URL="/&lt;vilib&gt;/gRPC/LabVIEW gRPC Library/Libraries/Win32/labview_grpc_server.dll"/>
			</Item>
			<Item Name="Win64" Type="Folder">
				<Item Name="feature_config.ini" Type="Document" URL="/&lt;vilib&gt;/gRPC/LabVIEW gRPC Library/Libraries/Win64/feature_config.ini"/>
				<Item Name="labview_grpc_server.dll" Type="Document" URL="/&lt;vilib&gt;/gRPC/LabVIEW gRPC Library/Libraries/Win64/labview_grpc_server.dll"/>
			</Item>
		</Item>
		<Item Name="Support Code" Type="Folder">
			<Item Name="xnet_can_bus_monitor_api_client.lvlib" Type="Library" URL="../xnet_can_bus_monitor_api_client/xnet_can_bus_monitor_api_client.lvlib"/>
		</Item>
		<Item Name="XNET Bus Monitor Client.lvlib" Type="Library" URL="../XNET Bus Monitor Client.lvlib"/>
		<Item Name="Dependencies" Type="Dependencies"/>
		<Item Name="Build Specifications" Type="Build">
			<Item Name="XNET Bus Monitor" Type="EXE">
				<Property Name="App_copyErrors" Type="Bool">true</Property>
				<Property Name="App_INI_aliasGUID" Type="Str">{C6AF87DB-5AA3-4A98-BF83-3F95AC9C6E35}</Property>
				<Property Name="App_INI_GUID" Type="Str">{9B1EA166-E3DB-4A1D-B874-956C625B2216}</Property>
				<Property Name="App_serverConfig.httpPort" Type="Int">8002</Property>
				<Property Name="App_serverType" Type="Int">0</Property>
				<Property Name="Bld_autoIncrement" Type="Bool">true</Property>
				<Property Name="Bld_buildCacheID" Type="Str">{B2B3E6B1-D54B-4580-883C-03D3873F4BB1}</Property>
				<Property Name="Bld_buildSpecName" Type="Str">XNET Bus Monitor</Property>
				<Property Name="Bld_excludeInlineSubVIs" Type="Bool">true</Property>
				<Property Name="Bld_excludeLibraryItems" Type="Bool">true</Property>
				<Property Name="Bld_excludePolymorphicVIs" Type="Bool">true</Property>
				<Property Name="Bld_localDestDir" Type="Path">/C/Projects/XNET-Bus-Monitor-gRPC-Example/Built/Client</Property>
				<Property Name="Bld_modifyLibraryFile" Type="Bool">true</Property>
				<Property Name="Bld_previewCacheID" Type="Str">{D5E6E0B0-7CCC-4A75-95F3-29B424BE1B5E}</Property>
				<Property Name="Bld_version.build" Type="Int">3</Property>
				<Property Name="Bld_version.major" Type="Int">1</Property>
				<Property Name="Destination[0].destName" Type="Str">XNET Bus Monitor.exe</Property>
				<Property Name="Destination[0].path" Type="Path">/C/Projects/XNET-Bus-Monitor-gRPC-Example/Built/Client/XNET Bus Monitor.exe</Property>
				<Property Name="Destination[0].path.type" Type="Str">&lt;none&gt;</Property>
				<Property Name="Destination[0].preserveHierarchy" Type="Bool">true</Property>
				<Property Name="Destination[0].type" Type="Str">App</Property>
				<Property Name="Destination[1].destName" Type="Str">Support Directory</Property>
				<Property Name="Destination[1].path" Type="Path">/C/Projects/XNET-Bus-Monitor-gRPC-Example/Built/Client/data</Property>
				<Property Name="Destination[1].path.type" Type="Str">&lt;none&gt;</Property>
				<Property Name="Destination[2].destName" Type="Str">Libraries</Property>
				<Property Name="Destination[2].path" Type="Path">/C/Projects/XNET-Bus-Monitor-gRPC-Example/Built/Client/Libraries</Property>
				<Property Name="Destination[2].path.type" Type="Str">&lt;none&gt;</Property>
				<Property Name="Destination[2].preserveHierarchy" Type="Bool">true</Property>
				<Property Name="DestinationCount" Type="Int">3</Property>
				<Property Name="Source[0].itemID" Type="Str">{AFBA7CB7-471E-4C43-8C33-8D2FCF3978B3}</Property>
				<Property Name="Source[0].type" Type="Str">Container</Property>
				<Property Name="Source[1].destinationIndex" Type="Int">0</Property>
				<Property Name="Source[1].itemID" Type="Ref">/My Computer/XNET Bus Monitor Client.lvlib/XNET Bus Monitor Example.vi</Property>
				<Property Name="Source[1].sourceInclusion" Type="Str">TopLevel</Property>
				<Property Name="Source[1].type" Type="Str">VI</Property>
				<Property Name="Source[2].Container.applyDestination" Type="Bool">true</Property>
				<Property Name="Source[2].Container.applyInclusion" Type="Bool">true</Property>
				<Property Name="Source[2].Container.depDestIndex" Type="Int">0</Property>
				<Property Name="Source[2].destinationIndex" Type="Int">2</Property>
				<Property Name="Source[2].itemID" Type="Ref">/My Computer/Libraries</Property>
				<Property Name="Source[2].sourceInclusion" Type="Str">Include</Property>
				<Property Name="Source[2].type" Type="Str">Container</Property>
				<Property Name="SourceCount" Type="Int">3</Property>
				<Property Name="TgtF_companyName" Type="Str">National Instruments</Property>
				<Property Name="TgtF_fileDescription" Type="Str">XNET Bus Monitor</Property>
				<Property Name="TgtF_internalName" Type="Str">XNET Bus Monitor</Property>
				<Property Name="TgtF_legalCopyright" Type="Str">Copyright © 2025 National Instruments</Property>
				<Property Name="TgtF_productName" Type="Str">XNET Bus Monitor</Property>
				<Property Name="TgtF_targetfileGUID" Type="Str">{184A2833-5F54-4CB5-AABE-ABA4617D7817}</Property>
				<Property Name="TgtF_targetfileName" Type="Str">XNET Bus Monitor.exe</Property>
				<Property Name="TgtF_versionIndependent" Type="Bool">true</Property>
			</Item>
		</Item>
	</Item>
</Project>
