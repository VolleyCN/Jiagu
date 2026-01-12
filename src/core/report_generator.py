#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
加固报告生成功能模块
负责生成加固报告，记录加固过程和结果
"""

import os
import time
import json
from datetime import datetime
from loguru import logger

class ReportGenerator:
    """
    加固报告生成器
    """
    
    def __init__(self):
        """
        初始化报告生成器
        """
        self.report_template = {
            'report_id': '',
            'generated_time': '',
            'total_apks': 0,
            'success_count': 0,
            'failed_count': 0,
            'options': {},
            'results': [],
            'summary': ''
        }
    
    def generate_report_id(self):
        """
        生成报告ID
        :return: 唯一报告ID
        """
        timestamp = int(time.time() * 1000)
        return f"jiagu_report_{timestamp}"
    
    def generate_report(self, results, output_dir, options=None):
        """
        生成加固报告
        :param results: 加固结果列表
        :param output_dir: 输出目录（已弃用，报告将始终保存到log目录）
        :param options: 加固选项
        :return: 报告文件路径
        """
        try:
            # 获取log目录路径
            log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "log")
            os.makedirs(log_dir, exist_ok=True)
            
            logger.info(f"开始生成加固报告，输出目录: {log_dir}")
            
            # 创建报告数据
            report = self.report_template.copy()
            report['report_id'] = self.generate_report_id()
            report['generated_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            report['total_apks'] = len(results)
            report['success_count'] = sum(1 for r in results if r['success'])
            report['failed_count'] = len(results) - report['success_count']
            report['options'] = options or {}
            report['results'] = results
            
            # 生成摘要
            report['summary'] = self._generate_summary(report)
            
            # 保存JSON格式报告
            json_report_path = os.path.join(log_dir, f"{report['report_id']}.json")
            with open(json_report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            logger.info(f"JSON报告生成成功: {json_report_path}")
            
            # 生成HTML格式报告
            html_report_path = os.path.join(log_dir, f"{report['report_id']}.html")
            self._generate_html_report(report, html_report_path)
            
            logger.info(f"HTML报告生成成功: {html_report_path}")
            
            # 生成简易文本报告
            txt_report_path = os.path.join(log_dir, f"{report['report_id']}.txt")
            self._generate_txt_report(report, txt_report_path)
            
            logger.info(f"文本报告生成成功: {txt_report_path}")
            
            return html_report_path  # 返回HTML报告路径，便于用户查看
        except Exception as e:
            logger.error(f"生成加固报告失败: {e}")
            return None
    
    def _generate_summary(self, report):
        """
        生成报告摘要
        :param report: 报告数据
        :return: 摘要文本
        """
        summary = f"""APK加固报告
================
报告ID: {report['report_id']}
生成时间: {report['generated_time']}

处理结果:
- 总APK数: {report['total_apks']}
- 成功数: {report['success_count']}
- 失败数: {report['failed_count']}

加固选项:
"""
        
        # 添加选项信息
        if report['options']:
            for key, value in report['options'].items():
                if key == 'signature':
                    summary += f"  - {key}: {'已配置' if value['keystore'] else '未配置'}\n"
                else:
                    summary += f"  - {key}: {'是' if value else '否'}\n"
        
        return summary
    
    def _generate_html_report(self, report, output_path):
        """
        生成HTML格式报告
        :param report: 报告数据
        :param output_path: 输出路径
        """
        html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>APK加固报告</title>
    <style>
        body {{ font-family: 'Microsoft YaHei', Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; border-bottom: 2px solid #4CAF50; padding-bottom: 10px; }}
        h2 {{ color: #555; margin-top: 30px; }}
        .summary {{ background-color: #e8f5e8; padding: 20px; border-radius: 5px; margin-bottom: 30px; }}
        .stats {{ display: flex; gap: 30px; margin: 20px 0; }}
        .stat-item {{ background-color: #f0f0f0; padding: 15px; border-radius: 5px; flex: 1; text-align: center; }}
        .stat-value {{ font-size: 24px; font-weight: bold; color: #4CAF50; }}
        .stat-label {{ color: #666; margin-top: 5px; }}
        .table-container {{ overflow-x: auto; margin: 20px 0; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background-color: #f2f2f2; font-weight: bold; }}
        tr:nth-child(even) {{ background-color: #f9f9f9; }}
        tr:hover {{ background-color: #f5f5f5; }}
        .success {{ color: #4CAF50; font-weight: bold; }}
        .failed {{ color: #f44336; font-weight: bold; }}
        .apks-info {{ margin: 20px 0; }}
        .options {{ background-color: #f0f8ff; padding: 20px; border-radius: 5px; margin: 20px 0; }}
        .options h3 {{ margin-top: 0; }}
        .option-item {{ margin: 10px 0; }}
        .footer {{ margin-top: 50px; text-align: center; color: #666; font-size: 14px; border-top: 1px solid #ddd; padding-top: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>APK加固报告</h1>
        
        <div class="summary">
            <p><strong>报告ID:</strong> {report['report_id']}</p>
            <p><strong>生成时间:</strong> {report['generated_time']}</p>
        </div>
        
        <h2>加固统计</h2>
        <div class="stats">
            <div class="stat-item">
                <div class="stat-value">{report['total_apks']}</div>
                <div class="stat-label">总APK数</div>
            </div>
            <div class="stat-item">
                <div class="stat-value success">{report['success_count']}</div>
                <div class="stat-label">成功数</div>
            </div>
            <div class="stat-item">
                <div class="stat-value failed">{report['failed_count']}</div>
                <div class="stat-label">失败数</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">{(report['success_count']/report['total_apks']*100) if report['total_apks'] > 0 else 0:.1f}%</div>
                <div class="stat-label">成功率</div>
            </div>
        </div>
        
        <h2>加固选项</h2>
        <div class="options">
            <h3>基本选项</h3>
            <div class="option-item"><strong>DEX加密:</strong> {'启用' if report['options'].get('dex_encrypt', False) else '禁用'}</div>
            <div class="option-item"><strong>资源混淆:</strong> {'启用' if report['options'].get('resource_obfuscate', False) else '禁用'}</div>
            <div class="option-item"><strong>防调试:</strong> {'启用' if report['options'].get('anti_debug', False) else '禁用'}</div>
            <div class="option-item"><strong>反Root:</strong> {'启用' if report['options'].get('anti_root', False) else '禁用'}</div>
            <div class="option-item"><strong>反模拟器:</strong> {'启用' if report['options'].get('anti_emulator', False) else '禁用'}</div>
            
            <h3>签名设置</h3>
            <div class="option-item"><strong>签名配置:</strong> {'已配置' if report['options'].get('signature', {}).get('keystore') else '未配置'}</div>
        </div>
        
        <h2>详细结果</h2>
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>序号</th>
                        <th>APK文件</th>
                        <th>状态</th>
                        <th>结果</th>
                        <th>输出目录</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        # 添加详细结果
        for i, result in enumerate(report['results'], 1):
            apk_name = os.path.basename(result['apk_path'])
            status = 'success' if result['success'] else 'failed'
            status_text = '成功' if result['success'] else '失败'
            message = result.get('message', result.get('error', ''))
            output_dir = result.get('output_dir', '')
            
            html_content += f"""
                    <tr>
                        <td>{i}</td>
                        <td>{apk_name}</td>
                        <td class="{status}">{status_text}</td>
                        <td>{message}</td>
                        <td>{output_dir}</td>
                    </tr>
            """
        
        # 结束HTML内容
        html_content += f"""
                </tbody>
            </table>
        </div>
        
        <div class="footer">
            <p>APK加固报告 - 生成时间: {report['generated_time']}</p>
        </div>
    </div>
</body>
</html>
        """
        
        # 写入HTML文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    def _generate_txt_report(self, report, output_path):
        """
        生成文本格式报告
        :param report: 报告数据
        :param output_path: 输出路径
        """
        txt_content = f"""APK加固报告
================
报告ID: {report['report_id']}
生成时间: {report['generated_time']}

一、加固统计
- 总APK数: {report['total_apks']}
- 成功数: {report['success_count']}
- 失败数: {report['failed_count']}
- 成功率: {(report['success_count']/report['total_apks']*100) if report['total_apks'] > 0 else 0:.1f}%

二、加固选项
- DEX加密: {'启用' if report['options'].get('dex_encrypt', False) else '禁用'}
- 资源混淆: {'启用' if report['options'].get('resource_obfuscate', False) else '禁用'}
- 防调试: {'启用' if report['options'].get('anti_debug', False) else '禁用'}
- 反Root: {'启用' if report['options'].get('anti_root', False) else '禁用'}
- 反模拟器: {'启用' if report['options'].get('anti_emulator', False) else '禁用'}
- 签名配置: {'已配置' if report['options'].get('signature', {}).get('keystore') else '未配置'}

三、详细结果
"""
        
        # 添加详细结果
        for i, result in enumerate(report['results'], 1):
            apk_name = os.path.basename(result['apk_path'])
            status = '成功' if result['success'] else '失败'
            message = result.get('message', result.get('error', ''))
            
            txt_content += f"""
{i}. {apk_name}
   状态: {status}
   结果: {message}
   原始路径: {result['apk_path']}
   输出目录: {result.get('output_dir', '')}
"""
        
        # 写入文本文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(txt_content)
    
    def get_report_summary(self, report_path):
        """
        获取报告摘要
        :param report_path: 报告文件路径
        :return: 报告摘要
        """
        try:
            if report_path.endswith('.json'):
                with open(report_path, 'r', encoding='utf-8') as f:
                    report = json.load(f)
                return report.get('summary', '')
            else:
                logger.error(f"不支持的报告格式: {report_path}")
                return None
        except Exception as e:
            logger.error(f"读取报告失败: {e}")
            return None
