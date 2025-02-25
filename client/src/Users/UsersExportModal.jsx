import { useState } from 'react';
import { parse } from 'csv-parse/browser/esm/sync';
import { saveAs } from 'file-saver'

import Api from '../Api';

function UsersExportModal ({ contest_id, is_tester, onClose }) {
  const [cols, setCols] = useState([]);
  const [emailCol, setEmailCol] = useState();
  const [idCol, setIdCol] = useState();
  const [file, setFile] = useState();

  function onChangeFile (event) {
    const [newFile] = event.target.files;
    const reader = new window.FileReader();
    reader.onload = (event) => {
      const csv = event.target.result;
      const data = parse(csv);
      setCols(data[0]);
    };
    reader.readAsText(newFile);
    setFile(newFile);
  }

  async function onExport () {
    const data = new FormData();
    data.append('contest_id', contest_id);
    data.append('is_tester', is_tester);
    data.append('email', emailCol);
    data.append('id', idCol);
    data.append('file', file);
    try {
      const response = await Api.export.users(data);
      saveAs(response.data, 'users_agg_with_ids.csv');
    } catch (err) {
      console.error(err);
    }
  }

  return (
    <>
      <div className='modal-backdrop fade show' />
      <div className='modal fade show d-block' tabIndex='-1'>
        <div className='modal-dialog modal-dialog-centered'>
          <div className='modal-content'>
            <div className='modal-header'>
              <h5 className='modal-title'>Export as CSV with Survey IDs</h5>
              <button onClick={onClose} type='button' className='btn-close' data-bs-dismiss='modal' aria-label='Close' />
            </div>
            <div className='modal-body'>
              <div className='mb-3'>
                <label htmlFor='survey-file'>Select survey data CSV with IDs here:</label>
                <input onChange={onChangeFile} type='file' className='form-control' id='survey-file' name='file' />
              </div>
              {cols.length > 0 && (
                <>
                  <div className='mb-3'>
                    <label htmlFor='survey-email-col'>Email column:</label>
                    <select className='form-select' id='survey-email' name='email' value={emailCol} onChange={(e) => setEmailCol(e.target.value)}>
                      {cols.map((col, index) => <option key={index} value={index}>{col}</option>)}
                    </select>
                  </div>
                  <div className='mb-3'>
                    <label htmlFor='survey-id-col'>ID column:</label>
                    <select className='form-select' id='survey-id' name='id' value={idCol} onChange={(e) => setIdCol(e.target.value)}>
                      {cols.map((col, index) => <option key={index} value={index}>{col}</option>)}
                    </select>
                  </div>
                </>
              )}
            </div>
            <div className='modal-footer'>
              <button onClick={onClose} type='button' className='btn btn-secondary' data-bs-dismiss='modal'>Close</button>
              <button onClick={onExport} disabled={!emailCol || !idCol} type='button' className='btn btn-primary'>Export</button>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

export default UsersExportModal;
