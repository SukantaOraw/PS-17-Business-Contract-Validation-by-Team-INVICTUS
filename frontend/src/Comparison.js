import React, { useState, useRef } from "react";
import { Button, Code, Divider } from "@nextui-org/react";

export default function Comparison() {
  const [file1, setFile1] = useState(null);
  const [file2, setFile2] = useState(null);
  const [message, setMessage] = useState("");
  const [similarParagraphs, setSimilarParagraphs] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [buttonState, setButtonState] = useState("Upload PDFs");

  const file1InputRef = useRef(null);
  const file2InputRef = useRef(null);

  const handleFile1Change = (event) => {
    setFile1(event.target.files[0]);
  };

  const handleFile2Change = (event) => {
    setFile2(event.target.files[0]);
  };

  const handleUpload = async () => {
    if (!file1 || !file2) {
      alert("Please upload both PDF files.");
      return;
    }

    setButtonState("Processing...");

    const formData = new FormData();
    formData.append("pdf1", file1);
    formData.append("pdf2", file2);

    try {
      setIsLoading(true);
      const response = await fetch("http://localhost:5000/upload", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error("Failed to upload PDF files.");
      }

      const data = await response.json();
      setMessage(data.message);
      setSimilarParagraphs(JSON.parse(data.similar_paragraphs) || []);
      setButtonState("Upload PDFs");
      // console.log(JSON.parse(data.similar_paragraphs));
    } catch (error) {
      console.error("Error uploading PDF files:", error);
      setMessage("Error uploading PDF files.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleFile1ButtonClick = () => {
    file1InputRef.current.click();
  };

  const handleFile2ButtonClick = () => {
    file2InputRef.current.click();
  };

  function wrapMarkedText(text) {
    if (!text) return '';
  
    return text.replace(/(<mark>.*?<\/mark>)(\s*<mark>.*?<\/mark>)*/g, (match) => {
      const combinedText = match.replace(/<\/?mark>/g, '');
      return `<span class="underline decoration-2 decoration-pink-500">${combinedText}</span>`;
    });
  }
  

  return (
    <div className="file-upload p-4 bg-gray-200 rounded-2xl">
      <div className="flex p-2 bg-slate-100 rounded-lg">
        <div className="flex space-x-2">
          <input
            type="file"
            onChange={handleFile1Change}
            ref={file1InputRef}
            style={{ display: "none" }}
          />
          <Button
            onClick={handleFile1ButtonClick}
            color="warning"
            variant="bordered"
          >
            {file1 ? `${file1.name}` : "Select PDF 1"}
          </Button>
          <input
            type="file"
            onChange={handleFile2Change}
            ref={file2InputRef}
            color="default"
            style={{ display: "none" }}
          />
          <Button
            onClick={handleFile2ButtonClick}
            color="warning"
            variant="bordered"
          >
            {file2 ? `${file2.name}` : "Select PDF 2"}
          </Button>
        </div>
        <div className="ml-auto">
          <Button onClick={handleUpload} color="primary" isLoading={isLoading}>
            {buttonState}
          </Button>
        </div>
      </div>

      {message && (
        <Code color="primary" variant="solid" className="my-3">
          {message}
        </Code>
      )}

      {similarParagraphs.length > 0 && (
        <div className="comparison_div_container flex flex-col gap-4 mt-2">
          
          <div className="flex gap-1 justify-between">
            <div className="max-w-[450px] min-w-[450px] p-2 bg-slate-300 rounded-lg font-bold text-slate-700">
              <h2 className="text-lg">Contract 1</h2>
            </div>
            <div className="max-w-[450px] min-w-[450px] p-2 bg-slate-300 rounded-lg font-bold text-slate-700">
              <h2 className="text-lg">Contract 2</h2>
            </div>            
          </div>

          {similarParagraphs.map((item, index) => (
            <>
            <div key={index} className="flex gap-1 justify-between">
              {item[3] ? (
                <div className="valComparePara">
                {item[1] && (
                  <p className="m-2 flex-grow" dangerouslySetInnerHTML={{ __html: wrapMarkedText(item[1]) }}></p>
                )}
                {item[1] && (
                  <p className="m-2 self-start">Predicted Clause: <i> <b>{item[2]}</b> </i></p>
                )}
              </div>
              
              ) : (
                <div className="delPara">
                  {item[1] && <p className="m-2 flex-grow">{item[1]}</p>}
                  {item[1] && <p className="m-2 self-start">Predicted Clause: <i> <b>{item[2]}</b> </i></p>}
                </div>
              )}

              <div className="mx-4 flex">
                {item[6] && (
                  <i className="self-center text-center bg-purple-600 p-2 text-white rounded-lg">
                    Similarity: {(item[6] * 100).toFixed(2)}%
                  </i>
                )}
                {item[1] && item[3] == null && (
                  <i className="self-center text-center bg-red-800 p-2 w-36 text-white rounded-lg">
                    Removed
                  </i>
                )}
                {item[1] == null && item[3] && (
                  <i className="self-center text-center bg-green-700 p-2 w-36 text-white rounded-lg">
                    Added
                  </i>)}
              </div>

              {item[1] ? (
                <div className="valComparePara">
                  {item[1] && item[4] && <p className="m-2 flex-grow" dangerouslySetInnerHTML={{ __html: wrapMarkedText(item[4]) }}></p>}
                  {item[3] && <p className="m-2 self-start">Predicted Clause: <i> <b>{item[5]}</b> </i></p>}
                </div>
              ) : (
                <div className="addPara">
                  {item[3] && <p className="m-2 flex-grow">{item[4]}</p>}
                  {item[3] && <p className="m-2 self-start">Predicted Clause: <i> <b>{item[5]}</b> </i></p>}
                </div>
              )}

            </div>
            <Divider />
            </>
          ))}
        </div>
      )}
    </div>
  );
}