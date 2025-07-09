import win32com.client as win32
import os


def convert_docx_to_txt_directly_with_word(docx_path, txt_path):
    """
    使用 Word COM 接口将 DOCX 文件直接另存为 TXT 文件。
    这应该与在 Word 中手动 "另存为 -> 纯文本" 的结果最接近。
    仅限 Windows，且需要安装 Microsoft Word。

    参数:
        docx_path (str): 输入的 DOCX 文件路径 (绝对路径)。
        txt_path (str): 输出的 TXT 文件路径 (绝对路径)。
    """
    word_app = None
    doc = None
    success = False
    try:
        abs_docx_path = os.path.abspath(docx_path)
        abs_txt_path = os.path.abspath(txt_path)

        print(f"INFO: 正在使用 Word COM 尝试将 '{abs_docx_path}' 另存为 '{abs_txt_path}'...")

        # 尝试 EnsureDispatch，它可能有助于加载类型库
        try:
            word_app = win32.gencache.EnsureDispatch("Word.Application")
        except AttributeError:  # 如果 gencache 或 EnsureDispatch 有问题，回退到 Dispatch
            print("WARN: win32.gencache.EnsureDispatch 失败，尝试 win32.Dispatch...")
            word_app = win32.Dispatch("Word.Application")

        word_app.Visible = False  # 不显示 Word 界面
        doc = word_app.Documents.Open(abs_docx_path)

        # FileFormat 参数:
        # wdFormatEncodedText 的数值是 7
        # Encoding 参数: 65001 代表 UTF-8
        doc.SaveAs2(abs_txt_path, FileFormat=7, Encoding=65001)  # <--- 修改在这里

        print(f"成功：文件已通过 Word COM 另存为 '{abs_txt_path}'")
        success = True
    except Exception as e:
        # 打印更详细的错误信息，包括错误类型
        print(f"错误类型: {type(e).__name__}")
        print(f"错误：使用 Word COM 另存为 TXT 失败 - {e}")
        if hasattr(e, 'com_error'):  # 专门处理 COM 错误
            print(f"COM Error Details: Code: {e.com_error.hresult}, Message: {e.com_error.description}")
        elif hasattr(e, 'args'):
            print(f"Error args: {e.args}")
    finally:
        if doc:
            doc.Close(False)  # False 表示不保存更改
        if word_app:
            word_app.Quit()
    return success


# --- 使用示例 ---
# !!! 请务必将下面的路径替换为您真实的 DOCX 文件路径 !!!
your_actual_docx_file = r"D:\download\china_register.docx"  # 例如： r"C:\path\to\your\document.docx"
# !!! 请确保这个文件路径是正确的 !!!

output_txt_via_com = os.path.splitext(your_actual_docx_file)[0] + "_word_saved.txt"

if os.name == 'nt':  # 检查是否为 Windows 系统
    if os.path.exists(your_actual_docx_file):
        if convert_docx_to_txt_directly_with_word(your_actual_docx_file, output_txt_via_com):
            print(f"\n请检查文件 '{output_txt_via_com}' 的内容。")
            try:
                with open(output_txt_via_com, "r", encoding="utf-8") as f:
                    print("\n--- 文件内容预览 (前1000字符) ---")  # 增加预览字符数
                    print(f.read(1000))
                    print("---------------------------------")
            except Exception as e:
                print(f"读取预览文件时出错: {e}")
    else:
        print(f"错误：输入文件 '{your_actual_docx_file}' 未找到。请检查路径是否正确！")
else:
    print("此 `win32com` 方法仅适用于 Windows 系统。")