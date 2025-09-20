#include <windows.h>
#include <stdlib.h>
#include <stdio.h>
#include<lmcons.h>
#include <direct.h>
#define MAXPATH  1024

void ComputerStart(char *pathName) {
	/*
	  添加pathName值为自启动注册表
	 */
	//找到系统的启动项
	char *szSubKey = "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run";
	HKEY hKey;

	//打开注册表启动项
	int k = RegOpenKeyExA(HKEY_CURRENT_USER, szSubKey, 0, KEY_ALL_ACCESS, &hKey);
	if (k == ERROR_SUCCESS) {
		//添加一个子Key,并设置值，MyStart为启动项名称，自定义设置；
		RegSetValueEx(hKey, "QuickAI", 0, REG_SZ, (BYTE *)pathName, strlen(pathName));

		//关闭注册表
		RegCloseKey(hKey);
		printf("自启动注册表设置成功\n");
	} else {
		printf("自启动注册表设置失败  error:%d\n", k);
	}
}

void cancel() {
	/*
	  取消自启动注册表
	 */
	// 找到系统的启动项
	char *szSubKey = "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run";
	HKEY hKey;

	// 打开注册表启动项
	int k = RegOpenKeyExA(HKEY_CURRENT_USER, szSubKey, 0, KEY_ALL_ACCESS, &hKey);
	if (k == ERROR_SUCCESS) {
		// 删除之前设置的启动项
		k = RegDeleteValueA(hKey, "QuickAI");
		if (k == ERROR_SUCCESS) {
			printf("已成功取消自启动\n");
		} else if (k == ERROR_FILE_NOT_FOUND) {
			printf("自启动项不存在\n");
		} else {
			printf("取消自启动失败  error:%d\n", k);
		}

		// 关闭注册表
		RegCloseKey(hKey);
	} else {
		printf("打开注册表失败  error:%d\n", k);
	}
}

int main(int argc, char *argv[]) {

	char buffer[MAXPATH];

	// 检查是否提供了命令行参数
	if (argc > 1) {
		// 将第一个参数复制到buffer中
		snprintf(buffer, MAXPATH, "%s", argv[1]);
		ComputerStart(buffer);
	} else {
		// 如果没有提供参数，取消自启动
		cancel();
	}
	
	return 0;
}
